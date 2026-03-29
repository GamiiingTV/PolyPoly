"""
PolyPoly — WebSocket Feed Temps Réel
Se connecte au WebSocket Polymarket et réagit en <1s aux mouvements de prix.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Callable, Optional
from loguru import logger

try:
    import websockets
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

from utils.database import Database

# WebSocket Polymarket — channel des prix en temps réel
POLYMARKET_WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"


class PriceUpdate:
    """Représente une mise à jour de prix en temps réel."""
    __slots__ = ["market_id", "token_id", "yes_price", "no_price",
                 "spread", "timestamp", "price_change"]

    def __init__(self, market_id, token_id, yes_price, no_price, spread, price_change=0.0):
        self.market_id = market_id
        self.token_id = token_id
        self.yes_price = yes_price
        self.no_price = no_price
        self.spread = spread
        self.timestamp = datetime.now(timezone.utc)
        self.price_change = price_change  # % de changement depuis dernière update


class RealtimeFeed:
    """
    Feed WebSocket temps réel Polymarket.

    Alimente tous les agents d'une mise à jour <1s au lieu de polling 60s.
    Détecte les mouvements soudains AVANT qu'ils soient intégrés au marché.
    """

    def __init__(self, db: Database):
        self.db = db
        self._running = False
        self._subscribed_tokens: set[str] = set()
        self._last_prices: dict[str, float] = {}     # token_id → dernier prix
        self._callbacks: list[Callable] = []          # Fonctions appelées sur update
        self._ws = None
        self._reconnect_delay = 2

    def add_callback(self, fn: Callable) -> None:
        """Enregistre une fonction callback appelée à chaque update de prix."""
        self._callbacks.append(fn)

    async def subscribe_markets(self, token_ids: list[str]) -> None:
        """Souscrit à des marchés supplémentaires."""
        new_tokens = set(token_ids) - self._subscribed_tokens
        if not new_tokens:
            return
        self._subscribed_tokens.update(new_tokens)

        if self._ws:
            await self._send_subscribe(list(new_tokens))

    async def _send_subscribe(self, token_ids: list[str]) -> None:
        """Envoie la commande de souscription au WebSocket."""
        if not self._ws:
            return
        sub_msg = {
            "type": "subscribe",
            "markets": [{"token_id": tid, "type": "price"} for tid in token_ids],
        }
        await self._ws.send(json.dumps(sub_msg))

    async def _auto_subscribe_top_markets(self) -> None:
        """Souscrit automatiquement aux 100 meilleurs marchés en DB."""
        markets = await self.db.get_active_markets(limit=100)
        token_ids = []
        for m in markets:
            raw = json.loads(m.get("raw_data", "{}"))
            ids = raw.get("clobTokenIds", [])
            token_ids.extend(ids)
        if token_ids:
            await self.subscribe_markets(token_ids[:200])
            logger.info(f"WebSocket: souscrit à {len(token_ids[:200])} tokens")

    async def run_forever(self) -> None:
        """Boucle WebSocket avec reconnexion automatique."""
        if not WS_AVAILABLE:
            logger.warning("websockets non installé — feed temps réel désactivé")
            return

        self._running = True
        logger.info("WebSocket Feed démarré")

        while self._running:
            try:
                await self._connect_and_listen()
            except Exception as e:
                if self._running:
                    logger.warning(f"WebSocket déconnecté: {e} — reconnexion dans {self._reconnect_delay}s")
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, 60)
            else:
                self._reconnect_delay = 2

    async def _connect_and_listen(self) -> None:
        """Connexion WebSocket et écoute des messages."""
        logger.info(f"WebSocket: connexion à {POLYMARKET_WS_URL}")

        async with websockets.connect(
            POLYMARKET_WS_URL,
            ping_interval=30,
            ping_timeout=10,
            close_timeout=5,
        ) as ws:
            self._ws = ws
            self._reconnect_delay = 2
            logger.info("WebSocket connecté")

            # Souscrire aux marchés en DB
            await self._auto_subscribe_top_markets()

            async for raw_msg in ws:
                if not self._running:
                    break
                try:
                    await self._process_message(raw_msg)
                except Exception as e:
                    logger.debug(f"WebSocket message erreur: {e}")

    async def _process_message(self, raw_msg: str) -> None:
        """Traite un message WebSocket."""
        try:
            data = json.loads(raw_msg)
        except json.JSONDecodeError:
            return

        msg_type = data.get("event_type") or data.get("type", "")

        if msg_type == "price_change":
            await self._handle_price_change(data)
        elif msg_type == "order_filled":
            await self._handle_order_filled(data)

    async def _handle_price_change(self, data: dict) -> None:
        """Réagit à un changement de prix."""
        token_id = data.get("asset_id") or data.get("token_id", "")
        new_price = float(data.get("price", 0))
        market_id = data.get("market_id", "")

        if not token_id or not new_price:
            return

        # Calculer le changement de prix
        old_price = self._last_prices.get(token_id, new_price)
        price_change = (new_price - old_price) / old_price if old_price > 0 else 0
        self._last_prices[token_id] = new_price

        # Enregistrer dans l'historique
        if market_id:
            await self.db.record_price(
                market_id=market_id,
                yes_price=new_price,
                no_price=1 - new_price,
                spread=abs(new_price - (1 - new_price)) * 0.02,
                volume=0,
            )

        # Déclencher les callbacks si mouvement significatif (>2%)
        if abs(price_change) > 0.02:
            update = PriceUpdate(
                market_id=market_id,
                token_id=token_id,
                yes_price=new_price,
                no_price=1 - new_price,
                spread=0.02,
                price_change=price_change,
            )
            for cb in self._callbacks:
                try:
                    asyncio.create_task(cb(update))
                except Exception as e:
                    logger.debug(f"WebSocket callback erreur: {e}")

    async def _handle_order_filled(self, data: dict) -> None:
        """Détecte les gros ordres remplis (activité baleine)."""
        size = float(data.get("size", 0))
        if size > 500:  # $500+ = grosse transaction
            logger.info(f"🐋 Gros ordre: ${size:.0f} sur {data.get('market_id', 'N/A')[:12]}")

    def stop(self) -> None:
        self._running = False


class FallbackPollingFeed:
    """
    Fallback si WebSocket indisponible — polling agressif toutes les 10s
    sur les marchés avec anomalie élevée.
    """

    def __init__(self, db: Database, gamma_api):
        self.db = db
        self.gamma = gamma_api
        self._running = False
        self._callbacks: list[Callable] = []
        self._last_prices: dict[str, float] = {}

    def add_callback(self, fn: Callable) -> None:
        self._callbacks.append(fn)

    async def run_forever(self) -> None:
        self._running = True
        logger.info("Polling Feed (fallback) démarré — intervalle: 10s")
        while self._running:
            try:
                await self._poll_hot_markets()
            except Exception as e:
                logger.debug(f"Polling erreur: {e}")
            await asyncio.sleep(10)

    async def _poll_hot_markets(self) -> None:
        """Poll les marchés avec le score d'anomalie le plus élevé."""
        from utils.polymarket_api import parse_market
        markets = await self.db.get_active_markets(limit=20)
        hot_markets = [m for m in markets if m.get("anomaly_score", 0) > 0.4]

        for market in hot_markets[:10]:
            try:
                raw = await self.gamma.get_market(market["id"])
                if not raw:
                    continue
                parsed = parse_market(raw)
                new_price = parsed["yes_price"]
                old_price = self._last_prices.get(market["id"], new_price)
                price_change = (new_price - old_price) / old_price if old_price > 0 else 0
                self._last_prices[market["id"]] = new_price

                if abs(price_change) > 0.03:
                    update = PriceUpdate(
                        market_id=market["id"],
                        token_id=market["id"],
                        yes_price=new_price,
                        no_price=1 - new_price,
                        spread=parsed["spread"],
                        price_change=price_change,
                    )
                    for cb in self._callbacks:
                        asyncio.create_task(cb(update))
            except Exception:
                continue

    def stop(self) -> None:
        self._running = False
