"""
HFT Feed Binance — WebSocket BTC/USDT temps réel.

Deux streams en parallèle :
  • btcusdt@trade       → tick par tick (price, volume, buyer/seller)
  • btcusdt@kline_5m    → bougies 5 minutes live + closed
"""

import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass, field
from typing import AsyncIterator, Callable, Optional

import websockets
from loguru import logger

from hft.config_hft import (
    BINANCE_WS_BASE,
    BINANCE_REST_BASE,
    BINANCE_SYMBOL_LOWER,
    CANDLE_LOOKBACK,
)

import httpx


# ── Structures de données ─────────────────────────────────────────────────────

@dataclass(slots=True)
class Tick:
    price: float
    qty: float
    timestamp_ms: int
    is_buyer_maker: bool   # True = sell trade (maker était acheteur = prix descend)


@dataclass
class Candle:
    time_ms: int           # Ouverture de la bougie (Unix ms)
    open: float
    high: float
    low: float
    close: float
    volume: float
    taker_buy_vol: float   # Volume côté acheteur taker
    closed: bool = False

    def update(self, price: float, qty: float, is_buyer_maker: bool) -> None:
        """Met à jour la bougie en cours avec un tick entrant."""
        self.close = price
        if price > self.high:
            self.high = price
        if price < self.low:
            self.low = price
        self.volume += qty
        if not is_buyer_maker:           # taker = acheteur aggressif
            self.taker_buy_vol += qty

    @property
    def taker_buy_ratio(self) -> float:
        return self.taker_buy_vol / self.volume if self.volume > 0 else 0.5

    @property
    def body_direction(self) -> float:
        """+1 bougie verte, -1 rouge, 0 neutre."""
        diff = self.close - self.open
        if abs(diff) < 0.001 * self.open:
            return 0.0
        return 1.0 if diff > 0 else -1.0


# ── Feed principal ────────────────────────────────────────────────────────────

class BinanceFeed:
    """
    Flux temps réel Binance pour BTCUSDT.

    Maintient :
      - Le dernier tick (price en quasi-temps-réel)
      - Un buffer de CANDLE_LOOKBACK bougies 5M fermées
      - La bougie 5M en cours (live)
    """

    COMBINED_WS = (
        f"{BINANCE_WS_BASE}/{BINANCE_SYMBOL_LOWER}@trade"
        f"/{BINANCE_SYMBOL_LOWER}@kline_5m"
    )

    def __init__(self) -> None:
        self.last_tick: Optional[Tick] = None
        self.last_price: float = 0.0
        self.last_ts_ms: int = 0

        # Buffer de bougies fermées (les 100 dernières)
        self.candles: deque[Candle] = deque(maxlen=CANDLE_LOOKBACK)
        # Bougie 5M en cours
        self.current_candle: Optional[Candle] = None

        self._tick_callbacks: list[Callable] = []
        self._candle_callbacks: list[Callable] = []  # appelé sur bougie fermée

        self._running = False
        self._reconnect_delay = 1.0
        self._ws: Optional[websockets.WebSocketClientProtocol] = None

    # ── API publique ──────────────────────────────────────────────────────────

    def on_tick(self, fn: Callable[[Tick], None]) -> None:
        self._tick_callbacks.append(fn)

    def on_candle_closed(self, fn: Callable[[Candle], None]) -> None:
        self._candle_callbacks.append(fn)

    async def bootstrap_candles(self) -> None:
        """Charge les CANDLE_LOOKBACK dernières bougies 5M via REST."""
        url = f"{BINANCE_REST_BASE}/api/v3/klines"
        params = {
            "symbol": BINANCE_SYMBOL_LOWER.upper(),
            "interval": "5m",
            "limit": CANDLE_LOOKBACK,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                for k in resp.json():
                    c = Candle(
                        time_ms=int(k[0]),
                        open=float(k[1]),
                        high=float(k[2]),
                        low=float(k[3]),
                        close=float(k[4]),
                        volume=float(k[5]),
                        taker_buy_vol=float(k[9]),
                        closed=True,
                    )
                    self.candles.append(c)
                logger.info(f"Binance: {len(self.candles)} bougies 5M chargées")
        except Exception as e:
            logger.warning(f"Bootstrap bougies Binance impossible: {e}")

    async def run_forever(self) -> None:
        """Boucle WebSocket avec reconnexion automatique."""
        self._running = True
        await self.bootstrap_candles()
        logger.info("Binance WebSocket démarré")

        while self._running:
            try:
                await self._connect_and_listen()
                self._reconnect_delay = 1.0
            except Exception as e:
                if self._running:
                    logger.warning(
                        f"Binance WS déconnecté: {e} "
                        f"— reconnexion dans {self._reconnect_delay:.0f}s"
                    )
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, 60.0)

    def stop(self) -> None:
        self._running = False

    # ── Interne ───────────────────────────────────────────────────────────────

    async def _connect_and_listen(self) -> None:
        logger.debug(f"Binance WS: connexion → {self.COMBINED_WS}")
        async with websockets.connect(
            self.COMBINED_WS,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=5,
            max_size=2**20,
        ) as ws:
            self._ws = ws
            async for raw in ws:
                if not self._running:
                    break
                await self._dispatch(raw)

    async def _dispatch(self, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except Exception:
            return

        stream = msg.get("stream", "")
        data = msg.get("data", msg)

        if "trade" in stream or data.get("e") == "trade":
            await self._on_trade(data)
        elif "kline" in stream or data.get("e") == "kline":
            await self._on_kline(data)

    async def _on_trade(self, data: dict) -> None:
        tick = Tick(
            price=float(data["p"]),
            qty=float(data["q"]),
            timestamp_ms=int(data["T"]),
            is_buyer_maker=bool(data["m"]),
        )
        self.last_tick = tick
        self.last_price = tick.price
        self.last_ts_ms = tick.timestamp_ms

        # Mise à jour de la bougie live
        if self.current_candle is not None:
            self.current_candle.update(tick.price, tick.qty, tick.is_buyer_maker)

        for cb in self._tick_callbacks:
            try:
                result = cb(tick)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception as e:
                logger.debug(f"Binance tick callback erreur: {e}")

    async def _on_kline(self, data: dict) -> None:
        k = data.get("k", {})
        candle = Candle(
            time_ms=int(k["t"]),
            open=float(k["o"]),
            high=float(k["h"]),
            low=float(k["l"]),
            close=float(k["c"]),
            volume=float(k["v"]),
            taker_buy_vol=float(k.get("V", 0)),
            closed=bool(k.get("x", False)),
        )

        if candle.closed:
            # Bougie fermée → archiver et notifier
            candle.closed = True
            self.candles.append(candle)
            self.current_candle = None
            logger.debug(
                f"Bougie 5M fermée: O={candle.open:.1f} H={candle.high:.1f} "
                f"L={candle.low:.1f} C={candle.close:.1f} V={candle.volume:.2f}"
            )
            for cb in self._candle_callbacks:
                try:
                    result = cb(candle)
                    if asyncio.iscoroutine(result):
                        asyncio.create_task(result)
                except Exception as e:
                    logger.debug(f"Binance candle callback erreur: {e}")
        else:
            # Bougie en cours → mettre à jour l'état live
            self.current_candle = candle

    # ── Getters utilitaires ───────────────────────────────────────────────────

    def get_closes(self) -> list[float]:
        """Dernières closes des bougies archivées (oldest → newest)."""
        return [c.close for c in self.candles]

    def get_highs(self) -> list[float]:
        return [c.high for c in self.candles]

    def get_lows(self) -> list[float]:
        return [c.low for c in self.candles]

    def get_volumes(self) -> list[float]:
        return [c.volume for c in self.candles]

    def get_taker_buy_ratios(self) -> list[float]:
        return [c.taker_buy_ratio for c in self.candles]

    def get_ohlcv(self) -> tuple[list, list, list, list, list]:
        return (
            [c.open for c in self.candles],
            [c.high for c in self.candles],
            [c.low for c in self.candles],
            [c.close for c in self.candles],
            [c.volume for c in self.candles],
        )

    def ready(self) -> bool:
        """True si on a assez de bougies pour calculer les indicateurs."""
        return len(self.candles) >= 50
