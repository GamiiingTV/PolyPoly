"""
HFT Bot — Orchestrateur principal BTC Polymarket UP/DOWN 5M.

Pipeline complet par tick Binance (<100ms) :

  1. BinanceFeed tick → update candles + lag_detector
  2. IndicatorEngine → calcul RSI/MACD/BB/EMA/etc sur 100 bougies (NumPy)
  3. SignalAggregator → injection dans ForceGraph (100 nœuds)
  4. ForceGraph.compute() → consensus BULL/BEAR + convergence
  5. LagDetector → fenêtre d'arbitrage ouverte ?
  6. RiskManager.evaluate_signal() → signal validé + sizing
  7. HFTExecutor.execute_directional() → ordre placé en <100ms

Conditions de skip :
  • Convergence < 0.65
  • Signaux contradictoires (contradiction_score > 0.4)
  • Liquidité < $5000
  • Spread > 2%
  • Limite quotidienne atteinte
  • Pas de fenêtre de lag détectée
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional

from loguru import logger

from hft.config_hft import (
    CAPITAL_USD,
    FORCE_GRAPH_CONVERGENCE_THRESHOLD,
    HFT_LOG_FILE,
    HFT_LOG_LEVEL,
    MIN_EDGE_PCT,
)
from hft.feeds.binance_feed import BinanceFeed, Tick, Candle
from hft.feeds.polymarket_clob_feed import PolymarketCLOBFeed, BTCMarket
from hft.feeds.cryptoquant_feed import CryptoQuantFeed
from hft.signals.indicators import IndicatorEngine
from hft.signals.tradingview_signals import TradingViewSignals
from hft.signals.force_graph import ForceGraph
from hft.signals.aggregator import SignalAggregator
from hft.execution.lag_detector import LagDetector
from hft.execution.executor import HFTExecutor
from hft.risk.risk_manager import RiskManager


# ── Configuration logging ──────────────────────────────────────────────────────

def _setup_logging() -> None:
    import sys
    logger.remove()
    logger.add(sys.stdout, level=HFT_LOG_LEVEL, colorize=True,
               format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level:<8}</level> | {message}")
    logger.add(HFT_LOG_FILE, level="DEBUG", rotation="50 MB", retention="7 days",
               format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {message}")


# ── Bot HFT ────────────────────────────────────────────────────────────────────

class HFTBot:
    """
    Bot HFT BTC Polymarket.

    Exploite le micro-déphasage entre :
      • Prix spot BTC (Binance WebSocket, <1ms)
      • Signaux du marché (TradingView 5M, CryptoQuant)
      • Repricing CLOB Polymarket (lag 150ms–3000ms)
    """

    def __init__(self) -> None:
        # ── Feeds ──────────────────────────────────────────────────────────────
        self.binance = BinanceFeed()
        self.poly_clob = PolymarketCLOBFeed()
        self.cryptoquant = CryptoQuantFeed()
        self.tv = TradingViewSignals()

        # ── Signaux ────────────────────────────────────────────────────────────
        self.ind_engine = IndicatorEngine()
        self.force_graph = ForceGraph()
        self.aggregator = SignalAggregator()

        # ── Exécution ──────────────────────────────────────────────────────────
        self.lag_detector = LagDetector()
        self.risk = RiskManager(capital=CAPITAL_USD)
        self.executor = HFTExecutor(risk_manager=self.risk)

        # ── État interne ────────────────────────────────────────────────────────
        self._running = False
        self._tick_count = 0
        self._last_stats_print = 0.0
        self._last_trade_ts: int = 0
        self._min_trade_interval_ms = 500   # 500ms entre trades sur même marché

        # Registre des callbacks
        self.binance.on_tick(self._on_tick)
        self.binance.on_candle_closed(self._on_candle_closed)

    # ── Démarrage ─────────────────────────────────────────────────────────────

    async def run(self) -> None:
        """Lance le bot complet."""
        _setup_logging()
        logger.info("=" * 60)
        logger.info("HFT BTC Polymarket Bot — démarrage")
        logger.info(f"Capital: ${CAPITAL_USD:.0f} | Risk/trade: {CAPITAL_USD * 0.005:.2f}$")
        logger.info(f"Seuil convergence: {FORCE_GRAPH_CONVERGENCE_THRESHOLD:.0%}")
        logger.info("=" * 60)

        # Démarrer le session HTTP de l'executor
        await self.executor.start()
        self._running = True

        # Lancer tous les feeds et la boucle principale en parallèle
        try:
            await asyncio.gather(
                self.binance.run_forever(),
                self.poly_clob.run_forever(),
                self.cryptoquant.run_forever(),
                self.tv.run_forever(),
                self._monitor_loop(),
            )
        except asyncio.CancelledError:
            logger.info("Bot arrêté (CancelledError)")
        except Exception as e:
            logger.error(f"Erreur critique bot: {e}", exc_info=True)
        finally:
            await self.stop()

    async def stop(self) -> None:
        self._running = False
        self.binance.stop()
        self.poly_clob.stop()
        self.cryptoquant.stop()
        self.tv.stop()
        await self.executor.close()
        await self.poly_clob.close()
        await self.cryptoquant.close()
        self._print_final_stats()
        logger.info("Bot arrêté proprement")

    # ── Callbacks Binance ─────────────────────────────────────────────────────

    def _on_tick(self, tick: Tick) -> None:
        """Callback synchrone sur chaque tick BTC — pipeline principal <100ms."""
        self._tick_count += 1
        start_ns = time.perf_counter_ns()

        # 1. Mettre à jour le lag detector
        self.lag_detector.on_binance_tick(tick.price, tick.timestamp_ms)

        # 2. Skip si pas assez de bougies
        if not self.binance.ready():
            return

        # 3. Calculer les indicateurs
        opens, highs, lows, closes, volumes = self.binance.get_ohlcv()
        if len(closes) < 26:   # minimum pour MACD
            return

        ind = self.ind_engine.compute(opens, highs, lows, closes, volumes)
        ind_signals = self.ind_engine.normalize(ind)

        # 4. Trouver le marché actif
        market = self.poly_clob.get_best_market()

        # 5. Mettre à jour le lag detector avec le prix Polymarket
        if market:
            self.lag_detector.on_polymarket_price(
                market.yes_price, market.last_update_ms
            )

        # 6. Estimer la probabilité vraie
        estimated_fair = self.lag_detector.get_estimated_fair_price()

        # 7. Injecter dans le force-graph
        self.aggregator.update(
            graph=self.force_graph,
            ind=ind,
            ind_signals=ind_signals,
            tv=self.tv.get_latest(),
            cq=self.cryptoquant.get_latest(),
            market=market,
            spot_price=tick.price,
            poly_yes_price=market.yes_price if market else 0.5,
            estimated_true_prob=estimated_fair,
        )

        # 8. Calculer le consensus force-graph
        consensus = self.force_graph.compute()

        # 9. Vérifier conditions de trading
        if not consensus.is_tradeable:
            return

        # 10. Vérifier fenêtre d'arbitrage
        edge_window = self.lag_detector.get_current_edge()
        if not edge_window:
            return

        # 11. Anti-spam : pas de trade trop rapproché
        now_ms = int(time.time() * 1000)
        if now_ms - self._last_trade_ts < self._min_trade_interval_ms:
            return

        # 12. Cohérence signal vs fenêtre d'arbitrage
        # La fenêtre doit pointer dans la même direction que le consensus
        if edge_window.direction != consensus.direction:
            logger.debug(
                f"Incohérence direction: force-graph={consensus.direction} "
                f"edge={edge_window.direction} → skip"
            )
            return

        # 13. Risk check + sizing (synchrone)
        if not market:
            return

        signal = self.risk.evaluate_signal(
            direction=consensus.direction,
            convergence=consensus.convergence,
            edge_pct=edge_window.edge_pct,
            market_id=market.market_id,
            liquidity_usd=market.liquidity_usd,
            spread_pct=market.spread_pct,
            contradiction_score=consensus.contradiction_score,
        )

        if signal is None:
            return

        # 14. Exécuter l'ordre (async — ne bloque pas la boucle tick)
        self._last_trade_ts = now_ms
        asyncio.ensure_future(
            self._execute_trade(signal, market, edge_window)
        )

        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        if elapsed_ms > 50:
            logger.debug(f"Pipeline tick: {elapsed_ms:.1f}ms")

    def _on_candle_closed(self, candle: Candle) -> None:
        """Appelé à chaque fermeture de bougie 5M."""
        logger.debug(
            f"Bougie fermée: O={candle.open:.1f} C={candle.close:.1f} "
            f"({'+' if candle.close > candle.open else '-'}"
            f"{abs(candle.close - candle.open) / candle.open * 100:.2f}%)"
        )

    # ── Exécution async ───────────────────────────────────────────────────────

    async def _execute_trade(self, signal, market, edge_window) -> None:
        """Exécute le trade de façon asynchrone."""
        start_ns = time.perf_counter_ns()
        result = await self.executor.execute_directional(
            market=market,
            signal=signal,
            edge_window=edge_window,
        )
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

        if result and result.success:
            logger.info(
                f"TRADE {signal.direction}: ${signal.size_usd:.2f} "
                f"@ {result.price:.4f} | {elapsed_ms:.1f}ms total | "
                f"edge={edge_window.edge_pct*100:.2f}%"
            )
        elif result:
            logger.warning(f"Trade échoué: {result.error}")

    # ── Monitoring ────────────────────────────────────────────────────────────

    async def _monitor_loop(self) -> None:
        """Stats périodiques toutes les 60s."""
        while self._running:
            await asyncio.sleep(60)
            self._print_stats()

    def _print_stats(self) -> None:
        risk = self.risk.get_stats()
        exec_stats = self.executor.stats
        lag = self.lag_detector.get_stats()
        markets = self.poly_clob.get_active_markets()
        best = self.poly_clob.get_best_market()

        logger.info("─" * 50)
        logger.info(
            f"Stats | Ticks={self._tick_count} | "
            f"Trades={exec_stats['orders_executed']} | "
            f"P&L={risk['daily_pnl']:+.2f}$ ({risk['daily_pnl_pct']:+.2f}%)"
        )
        logger.info(
            f"Lag moyen={lag['avg_lag_ms']:.0f}ms | "
            f"Fenêtres={lag['total_windows']} | "
            f"Marchés BTC={len(markets)}"
        )
        if best:
            logger.info(
                f"Marché: {best.question[:50]} | "
                f"YES={best.yes_price:.4f} | "
                f"Spread={best.spread_pct*100:.2f}% | "
                f"Liq=${best.liquidity_usd:.0f}"
            )
        if risk['halted']:
            logger.error(f"BOT HALTÉ: {risk['halt_reason']}")
        logger.info("─" * 50)

    def _print_final_stats(self) -> None:
        risk = self.risk.get_stats()
        exec_stats = self.executor.stats
        logger.info("=" * 60)
        logger.info("BILAN FINAL")
        logger.info(f"  P&L journalier : {risk['daily_pnl']:+.2f}$ ({risk['daily_pnl_pct']:+.2f}%)")
        logger.info(f"  Trades          : {risk['daily_trades']} (WR={risk['win_rate']*100:.0f}%)")
        logger.info(f"  Drawdown max    : {risk['max_drawdown']:.2f}$")
        logger.info(f"  USD total tradé : ${exec_stats['total_usd_executed']:.2f}")
        logger.info("=" * 60)
