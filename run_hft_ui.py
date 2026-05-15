#!/usr/bin/env python3
"""
PolyPoly HFT Bot — Interface terminal orange, deux stratégies.

Utilisation :
  python run_hft_ui.py                   # mode papier (pas de vrais ordres)
  python run_hft_ui.py --live            # mode live (nécessite POLYMARKET_API_KEY)
  python run_hft_ui.py --capital 150     # capital de départ personnalisé
  python run_hft_ui.py --live --capital 150

Deux stratégies en parallèle :
  • HFT Repricing  : capture le lag Binance→Polymarket (<100ms)
  • Resolution Snipe : achète YES/NO à 87¢ dans les 90s avant résolution
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
    FIXED_TRADE_USD,
)
from hft.dashboard import BotState, HFTDashboard
from hft.feeds.binance_feed import Tick
from hft.signals.resolution_sniper import ResolutionSniper


# ── Loguru → BotState sink ────────────────────────────────────────────────────

def _make_log_sink(state: BotState):
    def _sink(message):
        record = message.record
        level  = record["level"].name[:5]
        text   = record["message"]
        with state.lock:
            state.log_lines.append((level, text))
    return _sink


# ── HFTBotUI ─────────────────────────────────────────────────────────────────

class HFTBotUI(HFTBot):
    """
    HFTBot enrichi :
      - Met à jour BotState à chaque tick (thread-safe)
      - Intègre le Resolution Sniper en parallèle du HFT repricing
    """

    def __init__(self, state: BotState, trade_size: float) -> None:
        super().__init__()
        self._state      = state
        self._trade_size = trade_size
        self._sniper     = ResolutionSniper(trade_size_usd=trade_size)

    async def run(self) -> None:
        logger.remove()
        logger.add(sys.stderr, level="WARNING", colorize=False,
                   format="{time:HH:mm:ss} | {level:<5} | {message}")
        logger.add(_make_log_sink(self._state), level="INFO",
                   format="{message}")

        self._state.is_live = getattr(self.executor, "_live_mode", False)
        await super().run()

    # ── Pipeline tick ─────────────────────────────────────────────────────────

    def _on_tick(self, tick: Tick) -> None:
        s = self._state

        if s.btc_price > 0:
            s.btc_prev_price = s.btc_price
        s.btc_price      = tick.price
        s.btc_tick_count += 1
        s.pipeline_stage  = 1

        # Timer résolution pour affichage dashboard
        from hft.signals.resolution_sniper import ResolutionSniper
        s.snipe_seconds_left = ResolutionSniper.seconds_to_resolution()

        self._tick_count += 1
        start_ns = time.perf_counter_ns()

        # ── 1. Lag detector ────────────────────────────────────────────────────
        self.lag_detector.on_binance_tick(tick.price, tick.timestamp_ms)

        if not self.binance.ready():
            s.pipeline_stage = 0
            return

        opens, highs, lows, closes, volumes = self.binance.get_ohlcv()
        if len(closes) < 26:
            s.pipeline_stage = 0
            return

        # ── 2. Indicateurs ────────────────────────────────────────────────────
        s.pipeline_stage = 2
        ind         = self.ind_engine.compute(opens, highs, lows, closes, volumes)
        ind_signals = self.ind_engine.normalize(ind)

        # ── 3. Marché Polymarket ──────────────────────────────────────────────
        market = self.poly_clob.get_best_market()
        if market:
            self.lag_detector.on_polymarket_price(
                market.yes_price, market.last_update_ms
            )
            with s.lock:
                q = getattr(market, "question", None) or "BTC Market"
                s.market_name     = (q[:38] + "…") if len(q) > 40 else q
                s.poly_yes_price  = market.yes_price
                s.poly_spread_pct = market.spread_pct
                s.poly_liquidity  = market.liquidity_usd

        estimated_fair = self.lag_detector.get_estimated_fair_price()

        # ── 4. Force-graph ────────────────────────────────────────────────────
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

        lag_stats = self.lag_detector.get_stats()
        with s.lock:
            s.lag_ms               = lag_stats["avg_lag_ms"]
            s.lag_windows_detected = lag_stats["total_windows"]
            s.lag_active           = lag_stats["active_window"]

        # ── SNIPE : vérifier fenêtre de résolution ────────────────────────────
        if market and len(closes) >= 5 and self.risk.can_trade():
            snipe_sig = self._sniper.evaluate(
                btc_price=tick.price,
                btc_closes_4c=closes[-5:-1],
                poly_yes_price=market.yes_price,
            )
            if snipe_sig:
                asyncio.ensure_future(
                    self._execute_snipe_ui(snipe_sig, market)
                )

        # ── 5. EV+ Gate ───────────────────────────────────────────────────────
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

        # ── 6. Exécution HFT ──────────────────────────────────────────────────
        s.pipeline_stage = 5
        self._last_trade_ts = now_ms
        asyncio.ensure_future(
            self._execute_trade_ui(signal, market, edge_window)
        )

        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        if elapsed_ms > 80:
            logger.debug(f"Pipeline tick: {elapsed_ms:.1f}ms")

    # ── Exécution HFT repricing ───────────────────────────────────────────────

    async def _execute_trade_ui(self, signal, market, edge_window) -> None:
        s = self._state
        result = await self.executor.execute_directional(
            market=market,
            signal=signal,
            edge_window=edge_window,
        )
        s.pipeline_stage = 0

        entry = result.price if (result and result.success) else edge_window.poly_old_price

        trade = {
            "strat":     "HFT",
            "direction": "UP" if signal.direction == "BULL" else "DOWN",
            "entry":     entry,
            "exit":      entry,
            "pnl":       0.0,
            "btc_move":  edge_window.binance_move_pct * 100,
            "size_usd":  signal.size_usd,
            "status":    "placed" if (result and result.success) else "failed",
        }

        if result and result.success:
            with s.lock:
                s.total_trades += 1
                s.hft_trades   += 1
                s.recent_trades.append(trade)
                s.equity_history.append(s.capital)
                s.log_lines.append((
                    "TRADE",
                    f"HFT {'▲' if signal.direction=='BULL' else '▼'} "
                    f"${signal.size_usd:.0f} @ {entry:.4f}  "
                    f"edge={edge_window.edge_pct*100:.1f}%",
                ))
        elif result:
            with s.lock:
                s.log_lines.append(("WARN", f"HFT échoué : {result.error}"))

    # ── Exécution Resolution Snipe ────────────────────────────────────────────

    async def _execute_snipe_ui(self, snipe_sig, market) -> None:
        s = self._state

        # En mode papier : simuler directement
        if not getattr(self.executor, "_live_mode", False):
            entry = snipe_sig.entry_price
            trade = {
                "strat":     "SNP",
                "direction": "UP" if snipe_sig.direction == "BULL" else "DOWN",
                "entry":     entry,
                "exit":      entry,
                "pnl":       0.0,
                "btc_move":  snipe_sig.move_pct * 100,
                "size_usd":  snipe_sig.size_usd,
                "status":    "placed",
            }
            with s.lock:
                s.total_trades  += 1
                s.snipe_trades  += 1
                s.recent_trades.append(trade)
                s.equity_history.append(s.capital)
                s.log_lines.append((
                    "SNIPE",
                    f"SNP {'▲' if snipe_sig.direction=='BULL' else '▼'} "
                    f"${snipe_sig.size_usd:.0f} @ {entry:.3f}  "
                    f"⏱{snipe_sig.seconds_left:.0f}s  "
                    f"BTC{snipe_sig.move_pct*100:+.2f}%",
                ))
            return

        # En mode live : utiliser l'executor (token YES ou NO selon direction)
        from hft.risk.risk_manager import TradeSignal
        fake_signal = TradeSignal(
            direction=snipe_sig.direction,
            confidence=0.88,
            edge_pct=0.13,
            size_usd=snipe_sig.size_usd,
            market_id=market.market_id,
        )
        result = await self.executor.execute_directional(
            market=market,
            signal=fake_signal,
            edge_window=None,
        )
        entry = snipe_sig.entry_price

        trade = {
            "strat":     "SNP",
            "direction": "UP" if snipe_sig.direction == "BULL" else "DOWN",
            "entry":     entry,
            "exit":      entry,
            "pnl":       0.0,
            "btc_move":  snipe_sig.move_pct * 100,
            "size_usd":  snipe_sig.size_usd,
            "status":    "placed" if (result and result.success) else "failed",
        }

        with s.lock:
            s.total_trades += 1
            s.snipe_trades += 1
            s.recent_trades.append(trade)
            s.equity_history.append(s.capital)
            if result and result.success:
                s.log_lines.append((
                    "SNIPE",
                    f"SNP {'▲' if snipe_sig.direction=='BULL' else '▼'} "
                    f"${snipe_sig.size_usd:.0f} @ {entry:.3f}  "
                    f"⏱{snipe_sig.seconds_left:.0f}s",
                ))
            else:
                s.log_lines.append(("WARN", f"Snipe échoué : {getattr(result, 'error', '?')}"))

    # ── Monitor loop ──────────────────────────────────────────────────────────

    async def _monitor_loop(self) -> None:
        while self._running:
            await asyncio.sleep(2)
            stats = self.risk.get_stats()
            perp  = self.binance_perp.get()
            with self._state.lock:
                self._state.daily_pnl    = stats.get("daily_pnl", 0.0)
                self._state.capital      = self._state.capital_start + self._state.daily_pnl
                self._state.wins         = stats.get("wins", 0)
                self._state.losses       = stats.get("losses", 0)
                self._state.is_halted    = stats.get("halted", False)
                self._state.halt_reason  = stats.get("halt_reason", "")

                # Kelly stats
                self._state.kelly_size     = stats.get("kelly_size", 10.0)
                self._state.kelly_fraction = stats.get("kelly_fraction", 0.0)
                self._state.kelly_streak   = stats.get("kelly_streak", 0)
                self._state.kelly_burn_in  = stats.get("kelly_burn_in", True)
                self._state.kelly_rr       = stats.get("kelly_rr", 0.0)

                # Dérivés Binance Perpetuals
                self._state.funding_rate   = perp.funding_rate
                self._state.funding_signal = perp.funding_rate_signal
                self._state.oi_change_pct  = perp.oi_change_pct_5m
                self._state.whale_buy_btc  = perp.whale_buy_btc
                self._state.whale_sell_btc = perp.whale_sell_btc
                self._state.whale_pressure = perp.whale_pressure

                if self._state.daily_pnl != 0:
                    self._state.equity_history.append(self._state.capital)


# ── Thread bot ────────────────────────────────────────────────────────────────

def _run_bot_thread(state: BotState, trade_size: float) -> None:
    try:
        asyncio.run(_async_bot(state, trade_size))
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        with state.lock:
            state.log_lines.append(("ERROR", f"Bot crash: {exc}"))
            state.is_halted  = True
            state.halt_reason = str(exc)
        sys.stderr.write(f"\n[BOT THREAD CRASH]\n{tb}\n")
        sys.stderr.flush()


async def _async_bot(state: BotState, trade_size: float) -> None:
    bot  = HFTBotUI(state=state, trade_size=trade_size)
    loop = asyncio.get_running_loop()

    def _cancel():
        for task in asyncio.all_tasks(loop):
            task.cancel()

    for sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None)):
        if sig is None:
            continue
        try:
            loop.add_signal_handler(sig, _cancel)
        except (NotImplementedError, RuntimeError, ValueError):
            pass
    await bot.run()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="PolyPoly HFT — Dashboard")
    parser.add_argument("--live",    action="store_true",
                        help="Mode live (ordres réels)")
    parser.add_argument("--capital", type=float, default=CAPITAL_USD,
                        help=f"Capital de départ en USD (défaut={CAPITAL_USD})")
    parser.add_argument("--size",    type=float,
                        default=FIXED_TRADE_USD if FIXED_TRADE_USD > 0 else 10.0,
                        help="Taille par trade en USD (défaut=10$)")
    args = parser.parse_args()

    if args.live:
        import os
        if not os.getenv("POLYMARKET_API_KEY"):
            print("ERREUR : POLYMARKET_API_KEY absent du .env — mode live impossible.")
            sys.exit(1)

    state = BotState(
        capital_start=args.capital,
        capital=args.capital,
        is_live=args.live,
    )
    state.equity_history.append(args.capital)

    bot_thread = threading.Thread(
        target=_run_bot_thread,
        args=(state, args.size),
        daemon=True,
        name="HFTBotThread",
    )
    bot_thread.start()

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
        print("\nDashboard fermé — arrêt en cours…")
        bot_thread.join(timeout=5)
        print("Bye.")


if __name__ == "__main__":
    main()
