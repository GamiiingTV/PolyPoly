"""
HFT Risk Manager — Contrôles de risque agressifs.

Règles appliquées :
  • Risque par trade : 0.5% du capital
  • Limite quotidienne : 2% de perte max
  • Arrêt dur : -0.4% sur un trade unique
  • Pas de trade si :
    - limite quotidienne atteinte
    - circuit breaker déclenché
    - liquidité insuffisante
    - signaux contradictoires
    - spread trop large
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from hft.config_hft import (
    CAPITAL_USD,
    RISK_PER_TRADE_PCT,
    DAILY_RISK_LIMIT_PCT,
    HARD_STOP_PCT,
    RISK_PER_TRADE_USD,
    DAILY_LOSS_LIMIT_USD,
    HARD_STOP_USD,
    MIN_LIQUIDITY_USD,
    MAX_SPREAD_PCT,
    FORCE_GRAPH_CONVERGENCE_THRESHOLD,
    COMPOUND_ENABLED,
    RESERVE_PCT,
    MIN_POLY_ORDER_USD,
    FIXED_TRADE_USD,
    USE_KELLY,
)
from hft.risk.kelly_sizing import KellySizer, TradeOutcome


# ── Structures ────────────────────────────────────────────────────────────────

@dataclass
class TradeSignal:
    """Signal de trading généré par le bot."""
    direction: str        # "BULL" | "BEAR"
    confidence: float     # convergence force-graph [0, 1]
    edge_pct: float       # edge estimé [0, 1]
    size_usd: float       # montant à risquer
    market_id: str
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))


@dataclass
class TradeRecord:
    """Enregistrement d'un trade ouvert ou fermé."""
    order_id: str
    market_id: str
    direction: str
    entry_price: float
    size_usd: float
    entry_ts: int
    exit_price: Optional[float] = None
    exit_ts: Optional[int] = None
    pnl: Optional[float] = None
    status: str = "open"   # "open" | "resolved" | "cancelled"


@dataclass
class DailyStats:
    date: str
    pnl: float = 0.0
    trades: int = 0
    wins: int = 0
    losses: int = 0
    max_drawdown: float = 0.0
    peak_pnl: float = 0.0


# ── Risk Manager ──────────────────────────────────────────────────────────────

class RiskManager:
    """
    Gestion du risque pour le bot HFT Polymarket BTC.

    Usage :
        risk = RiskManager(capital=1000.0)
        signal = risk.evaluate_signal(direction, convergence, edge, market)
        if signal:
            await executor.execute_directional(market, signal, edge_window)
    """

    def __init__(self, capital: float = CAPITAL_USD) -> None:
        self.capital       = capital
        self._peak_capital = capital          # ATH capital pour drawdown compound
        self._daily_stats  = self._new_daily_stats()
        self._open_trades: dict[str, TradeRecord] = {}
        self._trade_history: list[TradeRecord] = []
        self._halted       = False
        self._halt_reason  = ""
        self._last_reset_date = self._today()
        # Kelly sizer (utilisé si USE_KELLY=true et burn-in passé)
        base_size = FIXED_TRADE_USD if FIXED_TRADE_USD > 0 else 10.0
        self._kelly = KellySizer(capital=capital, base_size=base_size)

    # ── Évaluation signal ─────────────────────────────────────────────────────

    def evaluate_signal(
        self,
        direction: str,
        convergence: float,
        edge_pct: float,
        market_id: str,
        liquidity_usd: float,
        spread_pct: float,
        contradiction_score: float,
    ) -> Optional[TradeSignal]:
        """
        Évalue si on peut trader et retourne un TradeSignal ou None.

        Rejette si :
          - Limite quotidienne atteinte
          - Bot halté (hard stop)
          - Convergence insuffisante
          - Signaux contradictoires
          - Liquidité faible
          - Spread trop large
          - Pas d'edge suffisant
        """
        self._check_daily_reset()

        # ── Bloquants durs ────────────────────────────────────────────────────
        if self._halted:
            logger.debug(f"Bot halté: {self._halt_reason}")
            return None

        if self._daily_stats.pnl <= -DAILY_LOSS_LIMIT_USD:
            if not self._halted:
                self._halt(f"Limite quotidienne atteinte: {self._daily_stats.pnl:.2f}$")
            return None

        # ── Qualité du signal ──────────────────────────────────────────────────
        if convergence < FORCE_GRAPH_CONVERGENCE_THRESHOLD:
            return None   # pas de log — trop fréquent

        if contradiction_score > 0.4:
            logger.debug(f"Signaux contradictoires: score={contradiction_score:.2f}")
            return None

        # ── Qualité du marché ─────────────────────────────────────────────────
        if liquidity_usd < MIN_LIQUIDITY_USD:
            logger.debug(f"Liquidité insuffisante: ${liquidity_usd:.0f} < ${MIN_LIQUIDITY_USD:.0f}")
            return None

        if spread_pct > MAX_SPREAD_PCT:
            logger.debug(f"Spread trop large: {spread_pct*100:.2f}% > {MAX_SPREAD_PCT*100:.1f}%")
            return None

        if edge_pct <= 0.003:
            return None   # pas assez d'edge

        # ── Calcul de la taille ───────────────────────────────────────────────
        size_usd = self._compute_position_size(convergence, edge_pct)
        if size_usd <= 0:
            return None

        signal = TradeSignal(
            direction=direction,
            confidence=convergence,
            edge_pct=edge_pct,
            size_usd=size_usd,
            market_id=market_id,
        )

        logger.info(
            f"Signal {direction}: conf={convergence:.3f} "
            f"edge={edge_pct*100:.2f}% size=${size_usd:.2f}"
        )
        return signal

    def _compute_position_size(self, confidence: float, edge_pct: float) -> float:
        """
        Position sizing Kelly-ajusté avec compound et réserve.

        Si FIXED_TRADE_USD > 0 : montant fixe par trade (ignore Kelly).
        Si COMPOUND_ENABLED :
          - Le capital actif = capital total × (1 - RESERVE_PCT)
          - La réserve est intouchable même si le capital augmente
          - Les positions grossissent automatiquement avec chaque gain
        """
        # ── Mode Kelly adaptatif ──────────────────────────────────────────────
        if USE_KELLY:
            size = self._kelly.suggest_size(self.capital)
            daily_limit = self.capital * DAILY_RISK_LIMIT_PCT
            remaining   = daily_limit + self._daily_stats.pnl
            size = min(size, max(0.0, remaining * 0.5))
            return max(0.0, round(size, 2))

        # ── Mode montant fixe ─────────────────────────────────────────────────
        if FIXED_TRADE_USD > 0:
            size = FIXED_TRADE_USD
            daily_limit = self.capital * DAILY_RISK_LIMIT_PCT
            remaining   = daily_limit + self._daily_stats.pnl
            size = min(size, max(0.0, remaining * 0.5))
            return max(0.0, round(size, 2))

        # Capital actif (hors réserve si compound activé)
        if COMPOUND_ENABLED:
            trading_capital = self.capital * (1.0 - RESERVE_PCT)
        else:
            trading_capital = self.capital

        # Base = RISK_PER_TRADE_PCT du capital actif
        base = trading_capital * RISK_PER_TRADE_PCT

        # Scale par la confiance (entre 0.65 et 1.0 → facteur 0.3x à 1.0x)
        conf_scale = (confidence - FORCE_GRAPH_CONVERGENCE_THRESHOLD) / (
            1.0 - FORCE_GRAPH_CONVERGENCE_THRESHOLD
        )
        conf_scale = max(0.3, min(1.0, conf_scale))

        # Scale par l'edge (entre 0.3% et 0.8% → facteur 0.3x à 1.0x)
        edge_scale = min(1.0, edge_pct / 0.005)
        edge_scale = max(0.3, edge_scale)

        size = base * conf_scale * edge_scale

        # Plancher minimum Polymarket (sinon ordre refusé)
        if size < MIN_POLY_ORDER_USD and size > 0:
            size = MIN_POLY_ORDER_USD

        # Plafond dynamique basé sur le capital actuel
        max_size = trading_capital * RISK_PER_TRADE_PCT * 2.0   # 2× la base max
        size = min(size, max_size)

        # Limite quotidienne restante
        daily_limit = self.capital * DAILY_RISK_LIMIT_PCT
        remaining   = daily_limit + self._daily_stats.pnl
        size = min(size, max(0.0, remaining * 0.5))

        return max(0.0, round(size, 2))

    def update_capital(self, new_capital: float) -> None:
        """
        Met à jour le capital (compound).

        À appeler après résolution d'un trade ou fin de session.
        Le capital augmente avec les gains → positions futures plus grosses.
        """
        if not COMPOUND_ENABLED:
            return
        old = self.capital
        self.capital = max(0.0, new_capital)
        self._peak_capital = max(self._peak_capital, self.capital)
        if self.capital != old:
            reserve = self.capital * RESERVE_PCT
            trading = self.capital * (1.0 - RESERVE_PCT)
            logger.info(
                f"Compound : capital {old:.2f}$ → {self.capital:.2f}$ "
                f"(réserve=${reserve:.2f} actif=${trading:.2f})"
            )

    # ── Enregistrement des trades ─────────────────────────────────────────────

    def record_order_placed(self, signal: TradeSignal, order_result) -> None:
        """Enregistre un ordre placé."""
        trade = TradeRecord(
            order_id=order_result.order_id or "unknown",
            market_id=signal.market_id,
            direction=signal.direction,
            entry_price=order_result.price,
            size_usd=signal.size_usd,
            entry_ts=int(time.time() * 1000),
        )
        self._open_trades[trade.order_id] = trade
        self._daily_stats.trades += 1

    def record_resolution(
        self,
        order_id: str,
        resolved_price: float,
    ) -> Optional[float]:
        """
        Enregistre la résolution d'un trade (marché clos).

        BTC plus haut → YES = 1.0 (gagne si BULL), NO = 0.0 (perd si BEAR)
        BTC plus bas  → YES = 0.0 (perd si BULL), NO = 1.0 (gagne si BEAR)
        """
        trade = self._open_trades.pop(order_id, None)
        if not trade:
            return None

        # P&L = (resolved_price - entry_price) * size / entry_price
        pnl = (resolved_price - trade.entry_price) / trade.entry_price * trade.size_usd

        trade.exit_price = resolved_price
        trade.exit_ts = int(time.time() * 1000)
        trade.pnl = pnl
        trade.status = "resolved"
        self._trade_history.append(trade)

        # Stats journalières
        self._daily_stats.pnl += pnl
        if pnl > 0:
            self._daily_stats.wins += 1
        else:
            self._daily_stats.losses += 1

        # Feed Kelly sizer pour adaptation
        self._kelly.record(TradeOutcome(pnl=pnl, size_usd=trade.size_usd))

        # ── Compound : mettre à jour le capital actif ─────────────────────────
        if COMPOUND_ENABLED:
            self.capital = max(0.0, self.capital + pnl)
            self._peak_capital = max(self._peak_capital, self.capital)

        # Mise à jour du drawdown
        if self._daily_stats.pnl > self._daily_stats.peak_pnl:
            self._daily_stats.peak_pnl = self._daily_stats.pnl
        drawdown = self._daily_stats.peak_pnl - self._daily_stats.pnl
        if drawdown > self._daily_stats.max_drawdown:
            self._daily_stats.max_drawdown = drawdown

        # Hard stop dynamique
        # En mode fixe, le max loss théorique = la mise ($5) — pas besoin d'un seuil plus bas.
        if FIXED_TRADE_USD > 0:
            hard_stop = FIXED_TRADE_USD
        elif COMPOUND_ENABLED:
            hard_stop = self.capital * HARD_STOP_PCT
        else:
            hard_stop = HARD_STOP_USD
        if pnl <= -hard_stop:
            logger.error(f"Hard stop déclenché: P&L={pnl:.2f}$ sur {order_id}")
            self._halt(f"Hard stop: perte de {pnl:.2f}$ sur un trade")

        level = "✓" if pnl > 0 else "✗"
        logger.info(
            f"{level} Trade résolu {trade.direction}: "
            f"P&L={pnl:+.2f}$ | "
            f"daily={self._daily_stats.pnl:+.2f}$"
        )
        return pnl

    # ── Contrôles ─────────────────────────────────────────────────────────────

    def can_trade(self) -> bool:
        self._check_daily_reset()
        if self._halted:
            return False
        if self._daily_stats.pnl <= -DAILY_LOSS_LIMIT_USD:
            return False
        return True

    def _halt(self, reason: str) -> None:
        self._halted = True
        self._halt_reason = reason
        logger.error(f"BOT HALTÉ : {reason}")

    def resume(self) -> None:
        """Reprend manuellement le trading (après intervention humaine)."""
        self._halted = False
        self._halt_reason = ""
        logger.info("Bot repris manuellement")

    def _check_daily_reset(self) -> None:
        today = self._today()
        if today != self._last_reset_date:
            logger.info(
                f"Reset journalier. Bilan J-1: "
                f"P&L={self._daily_stats.pnl:+.2f}$ "
                f"({self._daily_stats.wins}W/{self._daily_stats.losses}L)"
            )
            self._daily_stats = self._new_daily_stats()
            self._last_reset_date = today
            # Le halt se lève automatiquement chaque jour (sauf hard stop manuel)
            if "quotidienne" in self._halt_reason:
                self._halted = False
                self._halt_reason = ""

    @staticmethod
    def _today() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    def _new_daily_stats() -> DailyStats:
        return DailyStats(date=datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        win_rate = (
            self._daily_stats.wins / self._daily_stats.trades
            if self._daily_stats.trades > 0
            else 0.0
        )
        k = self._kelly.get_stats()
        return {
            "capital": self.capital,
            "daily_pnl": self._daily_stats.pnl,
            "daily_pnl_pct": self._daily_stats.pnl / self.capital * 100,
            "daily_trades": self._daily_stats.trades,
            "win_rate": win_rate,
            "wins": self._daily_stats.wins,
            "losses": self._daily_stats.losses,
            "max_drawdown": self._daily_stats.max_drawdown,
            "open_positions": len(self._open_trades),
            "halted": self._halted,
            "halt_reason": self._halt_reason,
            "risk_per_trade_usd": RISK_PER_TRADE_USD,
            "daily_limit_usd": DAILY_LOSS_LIMIT_USD,
            "hard_stop_usd": HARD_STOP_USD,
            "remaining_daily_budget": DAILY_LOSS_LIMIT_USD + self._daily_stats.pnl,
            "kelly_size":     k.suggested_size,
            "kelly_fraction": k.kelly_fraction,
            "kelly_streak":   k.streak,
            "kelly_burn_in":  k.using_burn_in,
            "kelly_rr":       k.rr_ratio,
        }
