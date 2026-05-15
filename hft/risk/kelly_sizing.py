"""
Kelly Adaptatif — sizing optimal basé sur les performances rolling.

Formule de Kelly :
    f* = (p × b - q) / b
    où p = win rate, q = 1-p, b = avg_win / avg_loss

Application :
  - On utilise une FRACTION de Kelly (0.5×) pour réduire la variance
  - On cap la taille à 5% du capital (sécurité)
  - On floor à $1 (minimum Polymarket)
  - On adapte aux streaks (réduit après 3 pertes, augmente après 5 gains)

Burn-in : avant 20 trades, on utilise la taille fixe HFT_FIXED_TRADE_USD.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Optional


import os

KELLY_FRACTION       = float(os.getenv("HFT_KELLY_FRACTION",  "0.50"))
MAX_POSITION_PCT     = float(os.getenv("HFT_KELLY_MAX_PCT",   "0.10"))  # max 10% capital
MIN_POSITION_USD     = float(os.getenv("HFT_MIN_ORDER_USD",   "1.0"))
BURN_IN_TRADES       = int(  os.getenv("HFT_KELLY_BURN_IN",   "20"))
ROLLING_WINDOW       = int(  os.getenv("HFT_KELLY_WINDOW",    "50"))
STREAK_LOSS_PENALTY  = float(os.getenv("HFT_KELLY_LOSS_PEN",  "0.60"))
STREAK_WIN_BONUS     = float(os.getenv("HFT_KELLY_WIN_BONUS", "1.25"))


@dataclass
class TradeOutcome:
    pnl: float
    size_usd: float
    strat: str = "HFT"            # "HFT" ou "SNP"


@dataclass
class KellyStats:
    win_rate:        float = 0.0
    avg_win:         float = 0.0
    avg_loss:        float = 0.0
    rr_ratio:        float = 0.0
    kelly_fraction:  float = 0.0
    suggested_size:  float = 0.0
    streak:          int   = 0     # >0 = gains consécutifs, <0 = pertes
    n_trades:        int   = 0
    using_burn_in:   bool  = True


class KellySizer:
    """
    Position sizer adaptatif.

    Usage :
        sizer = KellySizer(capital=150.0, base_size=10.0)
        sizer.record(TradeOutcome(pnl=+1.2, size_usd=10.0))
        size = sizer.suggest_size(capital=152.0)   # taille pour le prochain trade
    """

    def __init__(self, capital: float, base_size: float = 10.0) -> None:
        self._capital   = capital
        self._base_size = base_size
        self._history: deque[TradeOutcome] = deque(maxlen=ROLLING_WINDOW)
        self._streak: int = 0   # >0 wins, <0 losses
        self._last_stats = KellyStats(using_burn_in=True, suggested_size=base_size)

    # ── API publique ──────────────────────────────────────────────────────────

    def record(self, outcome: TradeOutcome) -> None:
        """À appeler après résolution de chaque trade."""
        self._history.append(outcome)
        if outcome.pnl > 0:
            self._streak = self._streak + 1 if self._streak >= 0 else 1
        else:
            self._streak = self._streak - 1 if self._streak <= 0 else -1

    def suggest_size(self, capital: float) -> float:
        """
        Retourne la taille suggérée pour le prochain trade.
        Met à jour les stats internes consultables via get_stats().
        """
        self._capital = capital
        n = len(self._history)

        # Burn-in : on garde la taille fixe
        if n < BURN_IN_TRADES:
            size = self._base_size
            self._last_stats = KellyStats(
                n_trades=n, using_burn_in=True, suggested_size=size,
                streak=self._streak,
            )
            return max(MIN_POSITION_USD, min(size, capital * MAX_POSITION_PCT))

        # Calcul WR et RR ratio sur l'historique
        wins   = [o.pnl for o in self._history if o.pnl > 0]
        losses = [abs(o.pnl) for o in self._history if o.pnl <= 0]

        wr      = len(wins) / n
        avg_w   = sum(wins)   / max(1, len(wins))
        avg_l   = sum(losses) / max(1, len(losses))
        rr      = avg_w / max(0.01, avg_l)

        # Kelly fraction
        if rr > 0 and wr > 0:
            f_full = (wr * rr - (1 - wr)) / rr
            f_full = max(0.0, f_full)
        else:
            f_full = 0.0

        # Fraction de Kelly (50%)
        f_used = f_full * KELLY_FRACTION

        # Taille brute = f × capital
        size = capital * f_used

        # Ajustement par streak
        if self._streak <= -3:
            size *= STREAK_LOSS_PENALTY
        elif self._streak >= 5:
            size *= STREAK_WIN_BONUS

        # Bornes
        size = min(size, capital * MAX_POSITION_PCT)
        size = max(size, MIN_POSITION_USD)

        # Fallback si Kelly négatif (edge négatif) : revenir à la base réduite
        if f_full <= 0:
            size = max(MIN_POSITION_USD, self._base_size * 0.5)

        self._last_stats = KellyStats(
            win_rate=wr,
            avg_win=avg_w,
            avg_loss=avg_l,
            rr_ratio=rr,
            kelly_fraction=f_full,
            suggested_size=size,
            streak=self._streak,
            n_trades=n,
            using_burn_in=False,
        )
        return round(size, 2)

    def get_stats(self) -> KellyStats:
        return self._last_stats
