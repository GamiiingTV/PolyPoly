"""
HFT Feed Polymarket CLOB — BTC UP/DOWN 5 minutes.

Responsabilités :
  • Trouver les marchés actifs "BTC +5min" via Gamma API
  • Suivre le carnet d'ordres via WebSocket CLOB
  • Détecter les repricing events (quand Polymarket s'ajuste)
  • Fournir : prix YES/NO, spread, profondeur, timestamp dernier update
"""

import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import httpx
import websockets
from loguru import logger

from hft.config_hft import (
    POLY_WS_URL,
    CLOB_REST_URL,
    GAMMA_API_URL,
    BTC_MARKET_KEYWORDS,
    MAX_RESOLUTION_WINDOW_SEC,
    MARKET_REFRESH_SEC,
)


# ── Structures ────────────────────────────────────────────────────────────────

@dataclass
class OrderBookLevel:
    price: float
    size: float


@dataclass
class BTCMarket:
    market_id: str
    question: str
    token_id_yes: str
    token_id_no: str
    yes_price: float = 0.5
    no_price: float = 0.5
    yes_bid: float = 0.0
    yes_ask: float = 1.0
    no_bid: float = 0.0
    no_ask: float = 1.0
    liquidity_usd: float = 0.0
    spread: float = 1.0
    last_update_ms: int = 0
    bids: list[OrderBookLevel] = field(default_factory=list)
    asks: list[OrderBookLevel] = field(default_factory=list)

    @property
    def mid_price(self) -> float:
        return self.yes_price

    @property
    def spread_pct(self) -> float:
        if self.yes_ask > 0:
            return (self.yes_ask - self.yes_bid) / self.yes_ask
        return 1.0

    @property
    def depth_imbalance(self) -> float:
        """
        Déséquilibre bid/ask de profondeur.
        +1 = plus de liquidité côté BUY (bull)
        -1 = plus de liquidité côté SELL (bear)
        """
        total_bid = sum(l.size for l in self.bids[:5])
        total_ask = sum(l.size for l in self.asks[:5])
        total = total_bid + total_ask
        if total == 0:
            return 0.0
        return (total_bid - total_ask) / total

    @property
    def age_ms(self) -> int:
        """Âge du dernier update en ms."""
        return int(time.time() * 1000) - self.last_update_ms


# ── Feed Polymarket CLOB ──────────────────────────────────────────────────────

class PolymarketCLOBFeed:
    """
    Flux CLOB Polymarket pour les marchés BTC 5M.

    Stratégie :
      1. Gamma API → chercher les marchés BTC 5M actifs
      2. CLOB REST  → snapshot orderbook initial
      3. CLOB WS    → updates prix en temps réel
    """

    def __init__(self) -> None:
        self._markets: dict[str, BTCMarket] = {}   # market_id → BTCMarket
        self._token_to_market: dict[str, str] = {}  # token_id → market_id
        self._running = False
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._reconnect_delay = 1.0

        # Historique des updates pour calculer la fréquence de repricing
        self._price_history: deque[tuple[int, float]] = deque(maxlen=200)

        # Dernier timestamp de mise à jour pour chaque token
        self._last_token_update_ms: dict[str, int] = {}

        # HTTP client partagé (connexion keep-alive)
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(5.0),
            limits=httpx.Limits(max_connections=20, keepalive_expiry=30),
        )

    # ── API publique ──────────────────────────────────────────────────────────

    def get_active_markets(self) -> list[BTCMarket]:
        return list(self._markets.values())

    def get_best_market(self) -> Optional[BTCMarket]:
        """Retourne le marché BTC 5M avec la meilleure liquidité."""
        markets = [m for m in self._markets.values() if m.liquidity_usd > 0]
        if not markets:
            return None
        return max(markets, key=lambda m: m.liquidity_usd)

    def get_current_yes_price(self, market_id: str) -> float:
        m = self._markets.get(market_id)
        return m.yes_price if m else 0.5

    def get_spread(self, market_id: str) -> float:
        m = self._markets.get(market_id)
        return m.spread_pct if m else 1.0

    def get_depth_imbalance(self, market_id: str) -> float:
        m = self._markets.get(market_id)
        return m.depth_imbalance if m else 0.0

    def get_last_update_age_ms(self, market_id: str) -> int:
        m = self._markets.get(market_id)
        return m.age_ms if m else 999999

    def get_repricing_frequency(self) -> float:
        """Updates par seconde sur les 60 dernières secondes."""
        if len(self._price_history) < 2:
            return 0.0
        now_ms = int(time.time() * 1000)
        recent = [ts for ts, _ in self._price_history if now_ms - ts < 60_000]
        return len(recent) / 60.0

    # ── Démarrage ─────────────────────────────────────────────────────────────

    async def run_forever(self) -> None:
        self._running = True
        logger.info("Polymarket CLOB Feed démarré")

        # Chargement initial des marchés
        await self._refresh_markets()

        # Tâches parallèles : WebSocket + refresh périodique des marchés
        await asyncio.gather(
            self._ws_loop(),
            self._market_refresh_loop(),
        )

    def stop(self) -> None:
        self._running = False

    # ── Recherche des marchés BTC 5M ─────────────────────────────────────────

    async def _refresh_markets(self) -> None:
        """Cherche les marchés BTC 5M actifs sur Polymarket."""
        try:
            resp = await self._http.get(
                f"{GAMMA_API_URL}/markets",
                params={
                    "active": "true",
                    "closed": "false",
                    "order": "volume24hr",
                    "ascending": "false",
                    "limit": 500,
                },
            )
            resp.raise_for_status()
            raw_markets = resp.json()
            if isinstance(raw_markets, dict):
                raw_markets = raw_markets.get("markets", [])

            found = 0
            valid_market_ids: set[str] = set()
            now_utc = datetime.now(timezone.utc)
            for raw in raw_markets:
                question = (raw.get("question") or "").lower()
                description = (raw.get("description") or "").lower()
                slug = (raw.get("slug") or "").lower()

                is_btc = any(kw in question or kw in description or kw in slug
                             for kw in BTC_MARKET_KEYWORDS)
                if not is_btc:
                    continue

                # Filtre court-terme : marché doit résoudre dans <= 1h
                # (sinon c'est un marché long-terme qui matche par accident)
                end_date_str = raw.get("endDate") or raw.get("end_date_iso") or ""
                if end_date_str:
                    try:
                        end_dt = datetime.fromisoformat(
                            end_date_str.replace("Z", "+00:00")
                        )
                        sec_to_resolve = (end_dt - now_utc).total_seconds()
                    except Exception:
                        continue
                    # Skip si > 1h ou déjà résolu il y a > 60s
                    if sec_to_resolve > 3600 or sec_to_resolve < -60:
                        continue
                else:
                    # Pas de date = on skip (trop risqué)
                    continue

                token_ids = raw.get("clobTokenIds", [])
                if isinstance(token_ids, str):
                    try:
                        token_ids = json.loads(token_ids)
                    except Exception:
                        token_ids = []
                if len(token_ids) < 2:
                    continue

                market_id = raw.get("id", "")
                if not market_id:
                    continue

                valid_market_ids.add(market_id)

                # Construire ou mettre à jour le marché
                if market_id not in self._markets:
                    market = BTCMarket(
                        market_id=market_id,
                        question=raw.get("question", ""),
                        token_id_yes=token_ids[0],
                        token_id_no=token_ids[1],
                        liquidity_usd=float(raw.get("liquidity", 0) or 0),
                    )
                    self._markets[market_id] = market
                    self._token_to_market[token_ids[0]] = market_id
                    self._token_to_market[token_ids[1]] = market_id
                else:
                    self._markets[market_id].liquidity_usd = float(
                        raw.get("liquidity", 0) or 0
                    )

                # Prix initiaux depuis Gamma
                prices = raw.get("outcomePrices", [])
                if isinstance(prices, str):
                    try:
                        prices = json.loads(prices)
                    except Exception:
                        prices = []
                if len(prices) >= 2:
                    try:
                        self._markets[market_id].yes_price = float(prices[0])
                        self._markets[market_id].no_price = float(prices[1])
                    except Exception:
                        pass

                found += 1

            # Purger les marchés expirés (plus dans la liste valide)
            stale = [mid for mid in self._markets if mid not in valid_market_ids]
            for mid in stale:
                old = self._markets.pop(mid, None)
                if old:
                    self._token_to_market.pop(old.token_id_yes, None)
                    self._token_to_market.pop(old.token_id_no, None)
            if stale:
                logger.info(f"Polymarket: {len(stale)} marchés expirés purgés")

            if found:
                logger.info(
                    f"Polymarket: {found} marchés BTC court-terme trouvés "
                    f"({len(self._markets)} total)"
                )
                for m in list(self._markets.values())[:5]:
                    logger.info(f"  → {m.question[:80]}")
                # Souscrire via WebSocket si connecté
                if self._ws:
                    await self._subscribe_all()
            else:
                logger.warning(
                    "Polymarket: aucun marché BTC court-terme actif "
                    "(résolution <1h) — réessai dans 30s"
                )

        except Exception as e:
            logger.warning(f"Polymarket refresh marchés: {e}")

    async def _market_refresh_loop(self) -> None:
        while self._running:
            await asyncio.sleep(MARKET_REFRESH_SEC)
            await self._refresh_markets()
            # Snapshot CLOB pour les marchés en portefeuille
            for market in self._markets.values():
                await self._fetch_orderbook_snapshot(market)

    # ── Snapshot CLOB (REST) ──────────────────────────────────────────────────

    async def _fetch_orderbook_snapshot(self, market: BTCMarket) -> None:
        """Snapshot REST du carnet d'ordres pour le token YES."""
        try:
            resp = await self._http.get(
                f"{CLOB_REST_URL}/book",
                params={"token_id": market.token_id_yes},
            )
            resp.raise_for_status()
            data = resp.json()
            self._apply_orderbook(market, data)
        except Exception as e:
            logger.debug(f"CLOB snapshot {market.market_id[:8]}: {e}")

    def _apply_orderbook(self, market: BTCMarket, data: dict) -> None:
        """Applique un snapshot ou update CLOB au marché."""
        bids_raw = data.get("bids", [])
        asks_raw = data.get("asks", [])

        market.bids = sorted(
            [OrderBookLevel(float(b["price"]), float(b["size"])) for b in bids_raw
             if b.get("price") and b.get("size")],
            key=lambda x: -x.price,
        )
        market.asks = sorted(
            [OrderBookLevel(float(a["price"]), float(a["size"])) for a in asks_raw
             if a.get("price") and a.get("size")],
            key=lambda x: x.price,
        )

        if market.bids:
            market.yes_bid = market.bids[0].price
        if market.asks:
            market.yes_ask = market.asks[0].price

        if market.yes_bid and market.yes_ask:
            market.yes_price = (market.yes_bid + market.yes_ask) / 2
            market.no_price = 1.0 - market.yes_price
            market.spread = market.yes_ask - market.yes_bid

        market.last_update_ms = int(time.time() * 1000)
        self._price_history.append((market.last_update_ms, market.yes_price))

    # ── WebSocket CLOB ────────────────────────────────────────────────────────

    async def _ws_loop(self) -> None:
        while self._running:
            try:
                await self._connect_ws()
                self._reconnect_delay = 1.0
            except Exception as e:
                if self._running:
                    logger.warning(
                        f"Polymarket WS déconnecté: {e} "
                        f"— reconnexion dans {self._reconnect_delay:.0f}s"
                    )
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, 30.0)

    async def _connect_ws(self) -> None:
        logger.debug(f"Polymarket WS: connexion → {POLY_WS_URL}")
        async with websockets.connect(
            POLY_WS_URL,
            ping_interval=30,
            ping_timeout=10,
            close_timeout=5,
            max_size=2**20,
        ) as ws:
            self._ws = ws
            await self._subscribe_all()
            async for raw in ws:
                if not self._running:
                    break
                await self._process_ws_message(raw)

    async def _subscribe_all(self) -> None:
        """Souscrit à tous les token_ids des marchés BTC 5M."""
        if not self._ws or not self._markets:
            return
        token_ids = []
        for m in self._markets.values():
            token_ids.extend([m.token_id_yes, m.token_id_no])

        msg = {
            "type": "subscribe",
            "markets": [{"token_id": tid, "type": "price_change"} for tid in token_ids],
        }
        try:
            await self._ws.send(json.dumps(msg))
            logger.debug(f"Polymarket WS: souscrit à {len(token_ids)} tokens")
        except Exception as e:
            logger.debug(f"Polymarket WS subscribe erreur: {e}")

    async def _process_ws_message(self, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except Exception:
            return

        event_type = msg.get("event_type") or msg.get("type", "")

        if event_type in ("price_change", "book"):
            await self._handle_price_change(msg)
        elif event_type == "tick_size_change":
            pass  # ignoré
        elif isinstance(msg, list):
            # Batch d'updates
            for item in msg:
                await self._process_ws_message(json.dumps(item))

    async def _handle_price_change(self, msg: dict) -> None:
        asset_id = msg.get("asset_id") or msg.get("token_id", "")
        if not asset_id:
            return

        market_id = self._token_to_market.get(asset_id)
        if not market_id:
            return

        market = self._markets.get(market_id)
        if not market:
            return

        new_price = msg.get("price")
        if new_price is not None:
            new_price = float(new_price)
            is_yes_token = (asset_id == market.token_id_yes)

            if is_yes_token:
                old = market.yes_price
                market.yes_price = new_price
                market.no_price = 1.0 - new_price
            else:
                market.no_price = new_price
                market.yes_price = 1.0 - new_price
                old = market.no_price

            market.last_update_ms = int(time.time() * 1000)
            self._last_token_update_ms[asset_id] = market.last_update_ms
            self._price_history.append((market.last_update_ms, market.yes_price))

            if abs(new_price - old) > 0.005:  # mouvement > 0.5%
                logger.debug(
                    f"CLOB reprice: {market.question[:40]} "
                    f"YES={market.yes_price:.4f} Δ={new_price - old:+.4f}"
                )

        # Si le message contient aussi le book complet
        if msg.get("bids") or msg.get("asks"):
            self._apply_orderbook(market, msg)

    async def close(self) -> None:
        self.stop()
        await self._http.aclose()
