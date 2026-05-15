"""
Binance Perpetuals Feed — données dérivées BTC USDT-M Futures.

Trois sources de signal :
  1. Funding rate  (REST  /fapi/v1/premiumIndex)  - polled 60s
       → Funding élevé (>0.01%) = trop de longs → signal bear
       → Funding négatif (<-0.005%) = trop de shorts → signal bull contrarian
  2. Open Interest (REST  /fapi/v1/openInterest)   - polled 30s
       → ΔOI + ΔPrice → divergence détecte la nature du mouvement
  3. Aggregated trades (WS  btcusdt@aggTrade)     - real-time
       → Trades > 1 BTC ($100k+) = whale activity
       → Buy pressure / sell pressure last 30s

Toutes les sources sont publiques, pas d'authentification.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import httpx
import websockets
from loguru import logger


PERP_REST = "https://fapi.binance.com"
PERP_WS   = "wss://fstream.binance.com/ws"
SYMBOL    = "BTCUSDT"

WHALE_BTC_THRESHOLD = 1.0      # 1 BTC ~ $100k
WHALE_WINDOW_SEC    = 30       # fenêtre rolling pour pression whale
OI_HISTORY_SAMPLES  = 6        # 6 × 30s = 3 minutes d'historique OI
FUNDING_BEAR_THRESH = 0.0001   # 0.01% funding = bear signal
FUNDING_BULL_THRESH = -0.00005 # -0.005% funding = bull contrarian


@dataclass
class WhaleTrade:
    timestamp_ms: int
    price: float
    qty_btc: float
    is_buy: bool   # True si market BUY (taker buy)


@dataclass
class PerpData:
    """Snapshot des dérivés à un instant t."""
    funding_rate:        float = 0.0     # taux courant
    funding_rate_signal: float = 0.0     # normalisé [-1, +1]
    next_funding_ms:     int   = 0
    mark_price:          float = 0.0

    open_interest_btc:   float = 0.0
    oi_change_pct_5m:    float = 0.0     # variation OI sur 5 min
    oi_signal:           float = 0.0     # normalisé [-1, +1]

    whale_buy_btc:       float = 0.0     # volume whale BUY 30s
    whale_sell_btc:      float = 0.0     # volume whale SELL 30s
    whale_count:         int   = 0
    whale_pressure:      float = 0.0     # [-1, +1]

    last_updated_ms:     int   = 0
    stale:               bool  = True


class BinancePerpFeed:
    """
    Poll les données dérivées Binance et expose un PerpData à jour.

    Usage :
        feed = BinancePerpFeed()
        await feed.start()             # lance les 3 tasks async
        data = feed.get()              # snapshot synchrone non-bloquant
    """

    def __init__(self) -> None:
        self._data = PerpData()
        self._oi_history: deque[tuple[float, float]] = deque(maxlen=OI_HISTORY_SAMPLES)
        self._whale_trades: deque[WhaleTrade] = deque(maxlen=200)
        self._running = False
        self._tasks: list[asyncio.Task] = []

    # ── API publique ──────────────────────────────────────────────────────────

    def get(self) -> PerpData:
        """Snapshot non-bloquant des données courantes."""
        # Recalcul whale pressure sur fenêtre 30s
        self._update_whale_pressure()
        return self._data

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._tasks = [
            asyncio.create_task(self._poll_funding_loop(), name="perp_funding"),
            asyncio.create_task(self._poll_oi_loop(),       name="perp_oi"),
            asyncio.create_task(self._ws_aggtrade_loop(),   name="perp_whale"),
        ]
        logger.info("BinancePerpFeed démarré : funding + OI + whale")

    async def stop(self) -> None:
        self._running = False
        for t in self._tasks:
            t.cancel()
        self._tasks.clear()

    # ── Funding rate ──────────────────────────────────────────────────────────

    async def _poll_funding_loop(self) -> None:
        async with httpx.AsyncClient(timeout=3.0) as client:
            while self._running:
                try:
                    r = await client.get(
                        f"{PERP_REST}/fapi/v1/premiumIndex",
                        params={"symbol": SYMBOL},
                    )
                    j = r.json()
                    rate = float(j.get("lastFundingRate", 0))
                    self._data.funding_rate    = rate
                    self._data.mark_price      = float(j.get("markPrice", 0))
                    self._data.next_funding_ms = int(j.get("nextFundingTime", 0))

                    # Normalisation contrarian :
                    # Funding > +0.0001 (longs payent shorts trop) → bear (-)
                    # Funding < -0.00005 (shorts payent longs)   → bull (+)
                    if rate > FUNDING_BEAR_THRESH:
                        sig = -min(1.0, (rate - FUNDING_BEAR_THRESH) / 0.0003)
                    elif rate < FUNDING_BULL_THRESH:
                        sig = min(1.0, (FUNDING_BULL_THRESH - rate) / 0.0003)
                    else:
                        sig = 0.0
                    self._data.funding_rate_signal = sig
                    self._data.last_updated_ms = int(time.time() * 1000)
                    self._data.stale = False
                except Exception as exc:
                    logger.debug(f"perp funding poll error: {exc}")
                await asyncio.sleep(60)

    # ── Open interest ─────────────────────────────────────────────────────────

    async def _poll_oi_loop(self) -> None:
        async with httpx.AsyncClient(timeout=3.0) as client:
            while self._running:
                try:
                    r = await client.get(
                        f"{PERP_REST}/fapi/v1/openInterest",
                        params={"symbol": SYMBOL},
                    )
                    j = r.json()
                    oi = float(j.get("openInterest", 0))
                    now = time.time()
                    self._oi_history.append((now, oi))
                    self._data.open_interest_btc = oi

                    # Variation sur 5 minutes (10 samples × 30s)
                    if len(self._oi_history) >= 2:
                        oldest = self._oi_history[0][1]
                        if oldest > 0:
                            change_pct = (oi - oldest) / oldest * 100
                            self._data.oi_change_pct_5m = change_pct
                            # OI hausse > 1% → confluence avec mouvement de prix
                            # OI baisse > 1% → unwinding → mean reversion
                            self._data.oi_signal = max(-1.0, min(1.0, change_pct / 2.0))
                except Exception as exc:
                    logger.debug(f"perp OI poll error: {exc}")
                await asyncio.sleep(30)

    # ── Whale aggregate trades (WebSocket) ────────────────────────────────────

    async def _ws_aggtrade_loop(self) -> None:
        url = f"{PERP_WS}/btcusdt@aggTrade"
        while self._running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    logger.info("WS aggTrade perp connecté")
                    async for raw in ws:
                        if not self._running:
                            break
                        try:
                            msg = json.loads(raw)
                            qty = float(msg.get("q", 0))
                            if qty >= WHALE_BTC_THRESHOLD:
                                is_buy = not msg.get("m", True)  # m=False → market buy
                                self._whale_trades.append(WhaleTrade(
                                    timestamp_ms=int(msg.get("T", time.time() * 1000)),
                                    price=float(msg.get("p", 0)),
                                    qty_btc=qty,
                                    is_buy=is_buy,
                                ))
                        except (json.JSONDecodeError, ValueError):
                            continue
            except Exception as exc:
                logger.debug(f"perp WS aggTrade disconnected: {exc} — reconnect 2s")
                await asyncio.sleep(2)

    def _update_whale_pressure(self) -> None:
        """Recalcule la pression whale sur fenêtre rolling 30s."""
        now_ms = int(time.time() * 1000)
        cutoff = now_ms - WHALE_WINDOW_SEC * 1000

        # Purge trades anciens
        while self._whale_trades and self._whale_trades[0].timestamp_ms < cutoff:
            self._whale_trades.popleft()

        buy_qty  = sum(w.qty_btc for w in self._whale_trades if w.is_buy)
        sell_qty = sum(w.qty_btc for w in self._whale_trades if not w.is_buy)
        total    = buy_qty + sell_qty

        self._data.whale_buy_btc  = buy_qty
        self._data.whale_sell_btc = sell_qty
        self._data.whale_count    = len(self._whale_trades)
        if total > 0:
            self._data.whale_pressure = (buy_qty - sell_qty) / total
        else:
            self._data.whale_pressure = 0.0
