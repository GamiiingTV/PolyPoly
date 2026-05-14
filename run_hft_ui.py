#!/usr/bin/env python3
"""
HFT Bot — Interface terminal « pirate » en temps réel.

Utilisation :
  python run_hft_ui.py                   # mode papier (pas de vrais ordres)
  python run_hft_ui.py --live            # mode live (nécessite POLYMARKET_API_KEY)
  python run_hft_ui.py --capital 200     # capital de départ personnalisé

Le dashboard riche tourne dans le thread principal.
Le bot HFT tourne en asyncio dans un thread secondaire.
L'état partagé (BotState) est mis à jour à chaque tick.
"""

from __future__ import annotations

import argparse
import asyncio
import signal
import sys
import threading
import time

sys.path.insert(0, ".")

from loguru import logger
from rich.live import Live

from hft.bot import HFTBot
from hft.config_hft import (
    CAPITAL_USD,
    FORCE_GRAPH_CONVERGENCE_THRESHOLD,
    MIN_EDGE_PCT,
)
from hft.dashboard import BotState, HFTDashboard
from hft.feeds.binance_feed import Candle, Tick


# ── Loguru → BotState sink ─────────────────────────────────────────────────────

def _make_log_sink(state: BotState):
    """Redirige les logs loguru vers le panneau EVENT LOG du dashboard."""
    def _sink(message):
        record = message.record
        level  = record["level"].name[:5]
        text   = record["message"]
        with state.lock:
            state.log_lines.append((level, text))
    return _sink


# ── Sous-classe HFTBot avec hooks dashboard ───────────────────────────────────

class HFTBotUI(HFTBot):
    """
    HFTBot enrichi : met à jour BotState à chaque tick et exécution.
    Le dashboard lit BotState en parallèle sans ralentir le pipeline.
    """

    def __init__(self, state: BotState) -> None:
        super().__init__()
        self._state = state

    async def run(self) -> None:
        # Ajouter le sink loguru → dashboard
        logger.remove()
        logger.add(sys.stderr, level="WARNING", colorize=False,
                   format="{time:HH:mm:ss} | {level:<5} | {message}")
        logger.add(_make_log_sink(self._state), level="INFO",
                   format="{message}")

        self._state.is_live = self.executor._live_mode if hasattr(self.executor, "_live_mode") else False
        await super().run()

    # ── Override _on_tick : copie du parent + injections état ────────────────

    def _on_tick(self, tick: Tick) -> None:
        s = self._state

        # BTC price
        if s.btc_price > 0:
            s.btc_prev_price = s.btc_price
        s.btc_price   = tick.price
        s.btc_tick_count += 1
        s.pipeline_stage = 1   # BINANCE

        self._tick_count += 1
        start_ns = time.perf_counter_ns()

        # ── Étape 1 : lag detector ────────────────────────────────────────────
        self.lag_detector.on_binance_tick(tick.price, tick.timestamp_ms)

        if not self.binance.ready():
            s.pipeline_stage = 0
            return

        opens, highs, lows, closes, volumes = self.binance.get_ohlcv()
        if len(closes) < 26:
            s.pipeline_stage = 0
            return

        # ── Étape 2 : indicateurs ─────────────────────────────────────────────
        s.pipeline_stage = 2
        ind         = self.ind_engine.compute(opens, highs, lows, closes, volumes)
        ind_signals = self.ind_engine.normalize(ind)

        # ── Étape 3 : marché Polymarket ───────────────────────────────────────
        market = self.poly_clob.get_best_market()
        if market:
            self.lag_detector.on_polymarket_price(
                market.yes_price, market.last_update_ms
            )
            with s.lock:
                q = getattr(market, "question", None) or "BTC Market"
                s.market_name   = (q[:38] + "…") if len(q) > 40 else q
                s.poly_yes_price  = market.yes_price
                s.poly_spread_pct = market.spread_pct
                s.poly_liquidity  = market.liquidity_usd

        estimated_fair = self.lag_detector.get_estimated_fair_price()

        # ── Étape 4 : force-graph ─────────────────────────────────────────────
        s.pipeline_stage = 3
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
        consensus = self.force_graph.compute()

        with s.lock:
            s.fg_field         = consensus.field
            s.fg_convergence   = consensus.convergence
            s.fg_direction     = consensus.direction
            s.fg_contradiction = consensus.contradiction_score

        # Mise à jour lag stats
        lag_stats = self.lag_detector.get_stats()
        with s.lock:
            s.lag_ms               = lag_stats["avg_lag_ms"]
            s.lag_windows_detected = lag_stats["total_windows"]
            s.lag_active           = lag_stats["active_window"]

        # ── Étape 5 : EV+ Gate ───────────────────────────────────────────────
        s.pipeline_stage = 4
        if not consensus.is_tradeable:
            s.pipeline_stage = 0
            return

        edge_window = self.lag_detector.get_current_edge()
        if not edge_window:
            s.pipeline_stage = 0
            return

        now_ms = int(time.time() * 1000)
        if now_ms - self._last_trade_ts < self._min_trade_interval_ms:
            s.pipeline_stage = 0
            return

        if edge_window.direction != consensus.direction:
            s.pipeline_stage = 0
            return

        if not market:
            s.pipeline_stage = 0
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
            s.pipeline_stage = 0
            return

        # ── Étape 6 : exécution ───────────────────────────────────────────────
        s.pipeline_stage = 5
        self._last_trade_ts = now_ms
        asyncio.ensure_future(
            self._execute_trade_ui(signal, market, edge_window)
        )

        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        if elapsed_ms > 80:
            logger.debug(f"Pipeline tick: {elapsed_ms:.1f}ms")

    async def _execute_trade_ui(self, signal, market, edge_window) -> None:
        """Exécute le trade et met à jour le dashboard."""
        s = self._state
        result = await self.executor.execute_directional(
            market=market,
            signal=signal,
            edge_window=edge_window,
        )
        s.pipeline_stage = 0

        entry = result.price if (result and result.success) else edge_window.poly_old_price

        trade = {
            "direction": "UP"   if signal.direction == "BULL" else "DOWN",
            "entry":     entry,
            "exit":      entry,                       # sera mis à jour à la résolution
            "pnl":       0.0,                         # inconnu avant résolution Polymarket
            "repriced":  True,
            "btc_move":  edge_window.binance_move_pct * 100,
            "size_usd":  signal.size_usd,
            "status":    "placed" if (result and result.success) else "failed",
        }

        if result and result.success:
            with s.lock:
                s.total_trades += 1
                s.recent_trades.append(trade)
                s.equity_history.append(s.capital)
                s.log_lines.append((
                    "TRADE",
                    f"{'▲' if signal.direction == 'BULL' else '▼'} {signal.direction} "
                    f"${signal.size_usd:.2f} @ {entry:.4f}  "
                    f"edge={edge_window.edge_pct*100:.1f}%",
                ))
        elif result:
            with s.lock:
                s.log_lines.append(("WARN", f"Trade échoué : {result.error}"))

    # ── Mise à jour periodique capital / stats ────────────────────────────────

    async def _monitor_loop(self) -> None:
        """Override : met à jour BotState en plus du monitoring normal."""
        while self._running:
            await asyncio.sleep(5)
            stats = self.risk.get_stats()
            with self._state.lock:
                # Capital = capital de départ + P&L journalier (proxy)
                self._state.daily_pnl = stats.get("daily_pnl", 0.0)
                self._state.capital   = self._state.capital_start + self._state.daily_pnl
                self._state.wins      = stats.get("win_rate", 0.0) * max(1, stats.get("daily_trades", 0))
                self._state.losses    = stats.get("daily_trades", 0) - self._state.wins
                self._state.is_halted = stats.get("halted", False)
                self._state.halt_reason = stats.get("halt_reason", "")
                if self._state.daily_pnl != 0:
                    self._state.equity_history.append(self._state.capital)


# ── Thread bot ─────────────────────────────────────────────────────────────────

_stop_event = threading.Event()


def _run_bot_thread(state: BotState) -> None:
    """Lance le bot HFT dans asyncio (thread secondaire)."""
    try:
        asyncio.run(_async_bot(state))
    except Exception as exc:
        with state.lock:
            state.log_lines.append(("ERROR", f"Bot thread crash: {exc}"))
            state.is_halted = True
            state.halt_reason = str(exc)


async def _async_bot(state: BotState) -> None:
    bot = HFTBotUI(state=state)

    # Gérer le stop propre
    loop = asyncio.get_running_loop()

    def _cancel():
        for task in asyncio.all_tasks(loop):
            task.cancel()

    loop.add_signal_handler(signal.SIGINT,  _cancel)
    loop.add_signal_handler(signal.SIGTERM, _cancel)

    await bot.run()


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="HFT BTC Polymarket — Dashboard UI")
    parser.add_argument("--live",    action="store_true", help="Mode live (ordres réels)")
    parser.add_argument("--capital", type=float, default=CAPITAL_USD,
                        help=f"Capital de départ en USD (défaut={CAPITAL_USD})")
    args = parser.parse_args()

    if args.live:
        import os
        if not os.getenv("POLYMARKET_API_KEY"):
            print("ERREUR : POLYMARKET_API_KEY absent du .env — mode live impossible.")
            sys.exit(1)

    # ── État partagé ──────────────────────────────────────────────────────────
    state = BotState(
        capital_start=args.capital,
        capital=args.capital,
        is_live=args.live,
    )
    state.equity_history.append(args.capital)

    # ── Lancer le bot en arrière-plan ─────────────────────────────────────────
    bot_thread = threading.Thread(
        target=_run_bot_thread,
        args=(state,),
        daemon=True,
        name="HFTBotThread",
    )
    bot_thread.start()

    # ── Dashboard dans le thread principal ────────────────────────────────────
    dashboard = HFTDashboard(state)

    try:
        with Live(
            dashboard.render(),
            refresh_per_second=4,
            screen=True,
            transient=False,
        ) as live:
            while bot_thread.is_alive():
                live.update(dashboard.render())
                time.sleep(0.25)

    except KeyboardInterrupt:
        pass
    finally:
        _stop_event.set()
        print("\nDashboard fermé — le bot s'arrête proprement...")
        bot_thread.join(timeout=5)
        print("Bye.")


if __name__ == "__main__":
    main()
