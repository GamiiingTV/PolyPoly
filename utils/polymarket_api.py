"""
PolyPoly — Wrapper Polymarket API
Gère les appels CLOB API + Gamma API avec retry automatique.
"""

import time
import hmac
import hashlib
import base64
import json
from typing import Optional
from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger

from config import (
    CLOB_API_URL, GAMMA_API_URL, POLYGON_RPC_URL,
    POLYMARKET_API_KEY, POLYMARKET_API_SECRET,
    POLYMARKET_API_PASSPHRASE, POLYMARKET_PRIVATE_KEY,
)


class PolymarketAPIError(Exception):
    pass


class GammaAPI:
    """Client pour l'API Gamma (données de marché, non-authentifiée)."""

    def __init__(self):
        self.base_url = GAMMA_API_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_markets(
        self,
        active: bool = True,
        limit: int = 100,
        offset: int = 0,
        order: str = "volume24hr",
        ascending: bool = False,
    ) -> list[dict]:
        params = {
            "active": str(active).lower(),
            "closed": "false",
            "limit": limit,
            "offset": offset,
            "order": order,
            "ascending": str(ascending).lower(),
        }
        resp = await self.client.get(f"{self.base_url}/markets", params=params)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else data.get("markets", [])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_market(self, market_id: str) -> Optional[dict]:
        try:
            resp = await self.client.get(f"{self.base_url}/markets/{market_id}")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError:
            return None

    async def get_all_active_markets(self, target: int = 300) -> list[dict]:
        """Récupère au moins `target` marchés actifs en paginant."""
        markets = []
        offset = 0
        batch = 100

        while len(markets) < target:
            batch_data = await self.get_markets(limit=batch, offset=offset)
            if not batch_data:
                break
            markets.extend(batch_data)
            offset += batch
            if len(batch_data) < batch:
                break

        logger.info(f"Gamma API: {len(markets)} marchés récupérés")
        return markets[:target] if len(markets) > target else markets

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_market_trades(self, market_id: str, limit: int = 50) -> list[dict]:
        params = {"market": market_id, "limit": limit}
        resp = await self.client.get(f"{self.base_url}/trades", params=params)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()


class CLOBAuth:
    """Authentification L1/L2 pour le CLOB Polymarket."""

    def __init__(self):
        self.api_key = POLYMARKET_API_KEY
        self.api_secret = POLYMARKET_API_SECRET
        self.api_passphrase = POLYMARKET_API_PASSPHRASE

    def get_headers(self, method: str, path: str, body: str = "") -> dict:
        timestamp = str(int(time.time() * 1000))
        message = timestamp + method.upper() + path + body

        mac = hmac.new(
            base64.b64decode(self.api_secret),
            message.encode("utf-8"),
            hashlib.sha256,
        )
        signature = base64.b64encode(mac.digest()).decode("utf-8")

        return {
            "POLY-API-KEY": self.api_key,
            "POLY-SIGNATURE": signature,
            "POLY-TIMESTAMP": timestamp,
            "POLY-PASSPHRASE": self.api_passphrase,
            "Content-Type": "application/json",
        }


class CLOBClient:
    """Client authentifié pour passer des ordres sur le CLOB Polymarket."""

    def __init__(self):
        self.base_url = CLOB_API_URL
        self.auth = CLOBAuth()
        self.client = httpx.AsyncClient(timeout=30.0)
        self._private_key = POLYMARKET_PRIVATE_KEY

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def get_orderbook(self, token_id: str) -> Optional[dict]:
        """Récupère le carnet d'ordres pour un token."""
        resp = await self.client.get(
            f"{self.base_url}/book",
            params={"token_id": token_id},
        )
        resp.raise_for_status()
        return resp.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def get_market_info(self, condition_id: str) -> Optional[dict]:
        resp = await self.client.get(f"{self.base_url}/markets/{condition_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_balance(self) -> float:
        """Retourne le solde USDC disponible."""
        path = "/balance"
        headers = self.auth.get_headers("GET", path)
        resp = await self.client.get(f"{self.base_url}{path}", headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("balance", 0))

    async def get_open_orders(self) -> list[dict]:
        path = "/orders"
        headers = self.auth.get_headers("GET", path)
        resp = await self.client.get(f"{self.base_url}{path}", headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def place_market_order(
        self,
        token_id: str,
        side: str,      # "BUY" ou "SELL"
        amount_usdc: float,
        price: float,   # Prix limite (0.0 à 1.0)
    ) -> dict:
        """
        Place un ordre marché.
        amount_usdc : montant en USDC à dépenser (max $5 par config)
        price : prix actuel pour calculer la quantité de shares
        """
        if not self._private_key:
            raise PolymarketAPIError("Clé privée non configurée — mode simulation")

        # Calcul de la quantité de shares
        shares = round(amount_usdc / price, 2) if price > 0 else 0

        order_body = {
            "orderType": "MARKET",
            "tokenID": token_id,
            "side": side,
            "amount": str(amount_usdc),
            "price": str(round(price, 4)),
        }

        body_str = json.dumps(order_body)
        path = "/order"
        headers = self.auth.get_headers("POST", path, body_str)

        resp = await self.client.post(
            f"{self.base_url}{path}",
            content=body_str,
            headers=headers,
        )

        if resp.status_code == 200:
            result = resp.json()
            logger.info(f"Ordre placé: {side} {shares} shares @ {price} — {token_id[:8]}...")
            return result
        else:
            raise PolymarketAPIError(f"Ordre échoué [{resp.status_code}]: {resp.text}")

    async def cancel_order(self, order_id: str) -> bool:
        path = f"/order/{order_id}"
        headers = self.auth.get_headers("DELETE", path)
        resp = await self.client.delete(f"{self.base_url}{path}", headers=headers)
        return resp.status_code == 200

    async def close(self):
        await self.client.aclose()


def parse_market(raw: dict) -> dict:
    """Normalise un marché brut de l'API Gamma en format interne."""
    outcomes = raw.get("outcomes", [])
    prices = raw.get("outcomePrices", [])

    yes_price = 0.5
    no_price = 0.5

    if isinstance(prices, list) and len(prices) >= 2:
        try:
            yes_price = float(prices[0])
            no_price = float(prices[1])
        except (ValueError, TypeError):
            pass
    elif isinstance(prices, str):
        try:
            parsed = json.loads(prices)
            if len(parsed) >= 2:
                yes_price = float(parsed[0])
                no_price = float(parsed[1])
        except Exception:
            pass

    spread = abs(yes_price - (1 - no_price))

    end_date = raw.get("endDate") or raw.get("endDateIso")

    # Construction de l'URL Polymarket
    group_slug = raw.get("groupSlug", "") or raw.get("group_slug", "")
    slug = raw.get("slug", "")
    if group_slug:
        market_url = f"https://polymarket.com/event/{group_slug}"
    elif slug:
        market_url = f"https://polymarket.com/market/{slug}"
    else:
        market_url = ""

    return {
        "id": raw.get("id", ""),
        "question": raw.get("question", "Unknown"),
        "category": raw.get("category", ""),
        "yes_price": yes_price,
        "no_price": no_price,
        "liquidity": float(raw.get("liquidity", 0) or 0),
        "volume_24h": float(raw.get("volume24hr", 0) or 0),
        "end_date": end_date,
        "active": 1 if raw.get("active", True) else 0,
        "anomaly_score": 0.0,
        "spread": spread,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "market_url": market_url,
        "token_id_yes": raw.get("clobTokenIds", [None])[0] if raw.get("clobTokenIds") else None,
        "token_id_no": raw.get("clobTokenIds", [None, None])[1] if raw.get("clobTokenIds") and len(raw.get("clobTokenIds", [])) > 1 else None,
    }
