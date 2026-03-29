"""
PolyPoly — Agent 6 : Order Book & Microstructure
La vraie alpha sur Polymarket est dans le carnet d'ordres.
Détecte les baleines, déséquilibres, et signaux de manipulation.
"""

import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Optional
from loguru import logger

from config import (
    MIN_LIQUIDITY_USD, MIN_CONFIDENCE_THRESHOLD,
    SCANNER_INTERVAL_SEC,
)
from utils.database import Database
from utils.polymarket_api import CLOBClient, GammaAPI, parse_market
try:
    from utils.telegram_bot import TelegramNotifier
except BaseException:
    TelegramNotifier = object  # type: ignore


# Seuils microstructure
WHALE_ORDER_THRESHOLD = 200       # $200+ = ordre baleine
IMBALANCE_STRONG = 0.70           # 70%+ d'un côté = fort signal directionnel
IMBALANCE_MODERATE = 0.55         # 55-70% = signal modéré
THIN_BOOK_THRESHOLD = 500         # Liquidité <$500 au meilleur niveau = livre mince
OBI_SIGNAL_THRESHOLD = 0.60       # Order Book Imbalance min pour signal
ORDERBOOK_SCAN_INTERVAL = 45      # secondes entre chaque scan profond


class OrderBookSnapshot:
    """Snapshot d'un carnet d'ordres à un instant T."""

    def __init__(self, market_id: str, bids: list, asks: list, timestamp: datetime):
        self.market_id = market_id
        self.bids = bids   # [(price, size), ...]
        self.asks = asks
        self.timestamp = timestamp

    @property
    def best_bid(self) -> float:
        return self.bids[0][0] if self.bids else 0.0

    @property
    def best_ask(self) -> float:
        return self.asks[0][0] if self.asks else 1.0

    @property
    def spread(self) -> float:
        return self.best_ask - self.best_bid

    @property
    def mid_price(self) -> float:
        return (self.best_bid + self.best_ask) / 2

    @property
    def bid_depth(self) -> float:
        """Volume total côté acheteur (en $)."""
        return sum(p * s for p, s in self.bids)

    @property
    def ask_depth(self) -> float:
        """Volume total côté vendeur (en $)."""
        return sum(p * s for p, s in self.asks)

    @property
    def order_book_imbalance(self) -> float:
        """
        OBI = (bid_depth - ask_depth) / (bid_depth + ask_depth)
        Positif → pression acheteuse → prix va monter
        Négatif → pression vendeuse → prix va baisser
        """
        total = self.bid_depth + self.ask_depth
        if total <= 0:
            return 0.0
        return (self.bid_depth - self.ask_depth) / total

    @property
    def whale_bid_volume(self) -> float:
        """Volume des gros ordres bid (>$200)."""
        return sum(p * s for p, s in self.bids if p * s >= WHALE_ORDER_THRESHOLD)

    @property
    def whale_ask_volume(self) -> float:
        """Volume des gros ordres ask (>$200)."""
        return sum(p * s for p, s in self.asks if p * s >= WHALE_ORDER_THRESHOLD)

    @property
    def is_thin(self) -> bool:
        """Livre trop mince pour trader sans slippage excessif."""
        return self.bid_depth < THIN_BOOK_THRESHOLD or self.ask_depth < THIN_BOOK_THRESHOLD


def parse_orderbook(raw: dict) -> tuple[list, list]:
    """Parse la réponse CLOB en listes (price, size)."""
    bids = []
    asks = []
    for level in raw.get("bids", []):
        try:
            price = float(level.get("price", 0))
            size = float(level.get("size", 0))
            if price > 0 and size > 0:
                bids.append((price, size))
        except (ValueError, TypeError):
            continue
    for level in raw.get("asks", []):
        try:
            price = float(level.get("price", 0))
            size = float(level.get("size", 0))
            if price > 0 and size > 0:
                asks.append((price, size))
        except (ValueError, TypeError):
            continue
    bids.sort(key=lambda x: -x[0])   # DESC
    asks.sort(key=lambda x: x[0])    # ASC
    return bids, asks


class OrderBookAgent:
    """
    Agent 6 — Analyse du carnet d'ordres.

    Responsabilités :
    - Récupère le carnet d'ordres CLOB en temps réel
    - Calcule l'Order Book Imbalance (OBI) — métrique clé
    - Détecte les ordres baleines (>$200)
    - Identifie les livres minces (risque de manipulation)
    - Génère des signaux directionnels basés sur la microstructure
    - Maintient un historique de l'OBI pour détecter les tendances
    """

    def __init__(self, db: Database, clob: CLOBClient,
                 gamma: GammaAPI, telegram: TelegramNotifier):
        self.db = db
        self.clob = clob
        self.gamma = gamma
        self.telegram = telegram
        self._running = False
        # Historique OBI par marché : market_id → deque[(timestamp, obi)]
        self._obi_history: dict[str, deque] = {}
        self._signals_generated = 0

    async def run_forever(self) -> None:
        """Boucle principale."""
        self._running = True
        logger.info("Agent 6 (OrderBook) démarré")
        while self._running:
            try:
                await self.orderbook_cycle()
            except Exception as e:
                logger.error(f"OrderBook erreur: {e}")
            await asyncio.sleep(ORDERBOOK_SCAN_INTERVAL)

    async def orderbook_cycle(self) -> list[dict]:
        """Analyse le carnet d'ordres des marchés les plus actifs."""
        markets = await self.db.get_active_markets(
            min_liquidity=MIN_LIQUIDITY_USD, limit=30
        )

        signals = []
        tasks = [self._analyze_market_orderbook(m) for m in markets[:20]]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, dict):
                signals.append(r)

        self._signals_generated += len(signals)
        if signals:
            logger.info(f"OrderBook: {len(signals)} signaux générés")

        return signals

    async def _analyze_market_orderbook(self, market: dict) -> Optional[dict]:
        """Analyse un marché spécifique."""
        import json

        market_id = market["id"]
        raw_data = json.loads(market.get("raw_data", "{}"))
        clob_token_ids = raw_data.get("clobTokenIds", [])

        if not clob_token_ids:
            return None

        token_id_yes = clob_token_ids[0] if clob_token_ids else None
        if not token_id_yes:
            return None

        # Récupérer le carnet d'ordres
        try:
            raw_book = await self.clob.get_orderbook(token_id_yes)
        except Exception as e:
            logger.debug(f"OrderBook {market_id[:8]}: {e}")
            return None

        if not raw_book:
            return None

        bids, asks = parse_orderbook(raw_book)
        if not bids or not asks:
            return None

        snap = OrderBookSnapshot(
            market_id=market_id,
            bids=bids,
            asks=asks,
            timestamp=datetime.now(timezone.utc),
        )

        # Enregistrer OBI dans l'historique
        if market_id not in self._obi_history:
            self._obi_history[market_id] = deque(maxlen=20)
        self._obi_history[market_id].append(
            (snap.timestamp, snap.order_book_imbalance)
        )

        # Générer signal si conditions remplies
        return await self._generate_signal(snap, market)

    async def _generate_signal(
        self, snap: OrderBookSnapshot, market: dict
    ) -> Optional[dict]:
        """Génère un signal de trading basé sur la microstructure."""

        obi = snap.order_book_imbalance
        abs_obi = abs(obi)

        # Pas de signal si OBI insuffisant
        if abs_obi < OBI_SIGNAL_THRESHOLD:
            return None

        # Pas de signal si livre trop mince (risque de manipulation)
        if snap.is_thin:
            logger.debug(f"Livre mince ignoré: {market['id'][:8]}")
            return None

        # Direction basée sur l'OBI
        direction = "YES" if obi > 0 else "NO"
        market_price = market.get("yes_price", 0.5)
        if direction == "NO":
            market_price = market.get("no_price", 0.5)

        # Facteur baleine
        whale_factor = 0.0
        if direction == "YES" and snap.whale_bid_volume > WHALE_ORDER_THRESHOLD:
            whale_factor = min(snap.whale_bid_volume / (snap.bid_depth + 1), 0.3)
        elif direction == "NO" and snap.whale_ask_volume > WHALE_ORDER_THRESHOLD:
            whale_factor = min(snap.whale_ask_volume / (snap.ask_depth + 1), 0.3)

        # Tendance OBI (est-ce que l'imbalance s'accélère ?)
        obi_trend = self._compute_obi_trend(snap.market_id)

        # Score de confiance composite
        base_confidence = 0.50 + abs_obi * 0.40 + whale_factor * 0.15 + obi_trend * 0.10
        confidence = min(base_confidence, 0.88)

        if confidence < MIN_CONFIDENCE_THRESHOLD:
            return None

        # Edge estimé : l'OBI prédit un mouvement de prix
        # Fort OBI → le prix devrait se déplacer vers la pression dominante
        estimated_price_move = abs_obi * 0.08  # 8% max de mouvement estimé
        edge = estimated_price_move * 0.6  # Conservatif

        signal = {
            "market_id": snap.market_id,
            "question": market.get("question", ""),
            "signal_type": "ORDERBOOK",
            "direction": direction,
            "confidence": round(confidence, 4),
            "edge": round(edge, 4),
            "predicted_prob": round(market_price + (edge if direction == "YES" else -edge), 4),
            "market_price": round(market_price, 4),
            "sentiment_score": 0.0,
            "source": (
                f"OBI={obi:.3f} | bid={snap.bid_depth:.0f}$ | ask={snap.ask_depth:.0f}$ "
                f"| spread={snap.spread:.3f} | whale=${snap.whale_bid_volume + snap.whale_ask_volume:.0f}"
            ),
            "obi": obi,
            "bid_depth": snap.bid_depth,
            "ask_depth": snap.ask_depth,
            "whale_volume": snap.whale_bid_volume + snap.whale_ask_volume,
            "spread": snap.spread,
        }

        await self.db.save_signal(signal)
        logger.info(
            f"Signal OB [{confidence:.2%}]: {direction} "
            f"{market['question'][:50]} | OBI={obi:.3f}"
        )

        # Alerte Telegram pour très fort signal
        if confidence > 0.82 or whale_factor > 0.2:
            await self.telegram.notify_opportunity(signal)

        return signal

    def _compute_obi_trend(self, market_id: str) -> float:
        """
        Calcule la tendance de l'OBI sur les dernières mesures.
        Positif = OBI s'intensifie (momentum fort)
        Négatif = OBI s'atténue (signal faible)
        """
        history = self._obi_history.get(market_id)
        if not history or len(history) < 4:
            return 0.0

        obis = [obi for _, obi in list(history)[-6:]]
        if len(obis) < 2:
            return 0.0

        # Pente linéaire simple
        n = len(obis)
        slope = (obis[-1] - obis[0]) / n
        return min(max(slope * 5, -1.0), 1.0)

    async def get_orderbook_features(self, market_id: str) -> dict:
        """
        Retourne les features d'order book pour le modèle XGBoost.
        Appelé par l'Agent 3 pour enrichir ses features.
        """
        import json
        market = await self.db.get_market(market_id)
        if not market:
            return {}

        raw_data = json.loads(market.get("raw_data", "{}"))
        clob_token_ids = raw_data.get("clobTokenIds", [])
        if not clob_token_ids:
            return {}

        try:
            raw_book = await self.clob.get_orderbook(clob_token_ids[0])
            if not raw_book:
                return {}
            bids, asks = parse_orderbook(raw_book)
            snap = OrderBookSnapshot(market_id, bids, asks, datetime.now(timezone.utc))
            obi_trend = self._compute_obi_trend(market_id)

            return {
                "obi": snap.order_book_imbalance,
                "bid_depth": snap.bid_depth,
                "ask_depth": snap.ask_depth,
                "ob_spread": snap.spread,
                "whale_bid_ratio": snap.whale_bid_volume / (snap.bid_depth + 1),
                "whale_ask_ratio": snap.whale_ask_volume / (snap.ask_depth + 1),
                "depth_ratio": snap.bid_depth / (snap.ask_depth + 1),
                "is_thin": int(snap.is_thin),
                "obi_trend": obi_trend,
                "n_bid_levels": len(bids),
                "n_ask_levels": len(asks),
            }
        except Exception:
            return {}

    def stop(self) -> None:
        self._running = False
        logger.info("Agent 6 (OrderBook) arrêté")
