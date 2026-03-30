"""
PolyPoly — Agent 15 : Smart Money Tracker
Suit les grosses positions des traders profitables sur Polymarket.
Quand plusieurs gros wallets misent dans la même direction → signal fort.
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Optional
from loguru import logger
import httpx

from utils.database import Database
from config import CLOB_API_URL

SCAN_INTERVAL_SEC = 900         # toutes les 15 minutes
MIN_TRADE_SIZE_USD = 100        # trade considéré "gros" si > $100
MIN_WALLETS_ALIGNED = 2         # au moins 2 gros wallets dans la même direction
LOOKBACK_HOURS = 6              # fenêtre d'analyse : dernières 6h
BASE_CONFIDENCE = 0.66
SIGNAL_COOLDOWN_SEC = 3600      # 1h entre signaux pour le même marché


class SmartMoneyAgent:
    """
    Agent 15 — Smart Money / Copy Trading.

    Pour chaque marché actif :
    - Récupère les trades récents via le CLOB Polymarket
    - Identifie les trades > $100 (gros traders)
    - Si ≥2 wallets distincts misent dans la même direction → signal SMART_MONEY
    - Confiance proportionnelle au nombre de wallets alignés et au volume
    """

    def __init__(self, db: Database, telegram):
        self.db = db
        self.telegram = telegram
        self._http = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
        self._running = False
        self._last_signal: dict[str, datetime] = {}  # market_id → last signal time

    async def run_forever(self):
        self._running = True
        logger.info("Agent 15 (Smart Money) démarré")
        while self._running:
            try:
                await self._scan_cycle()
            except Exception as e:
                logger.warning(f"SmartMoney erreur: {e}")
            await asyncio.sleep(SCAN_INTERVAL_SEC)

    async def _scan_cycle(self):
        markets = await self.db.get_active_markets(limit=60)
        signals_found = 0
        now = datetime.now(timezone.utc)

        for market in markets:
            market_id = market.get("id", "")

            # Anti-doublon
            last = self._last_signal.get(market_id)
            if last and (now - last).total_seconds() < SIGNAL_COOLDOWN_SEC:
                continue

            signal = await self._analyze_smart_money(market)
            if signal:
                self._last_signal[market_id] = now
                await self.db.save_signal(signal)
                signals_found += 1
                if signal["confidence"] >= 0.70:
                    await self.telegram.notify_opportunity(signal)

            await asyncio.sleep(0.5)  # Respecter le rate limit CLOB

        if signals_found:
            logger.info(f"SmartMoney: {signals_found} signal(s) généré(s)")

    async def _analyze_smart_money(self, market: dict) -> Optional[dict]:
        """Analyse les trades récents d'un marché et détecte les smart money."""
        raw_data = market.get("raw_data", "{}")
        if isinstance(raw_data, str):
            try:
                raw = json.loads(raw_data)
            except Exception:
                raw = {}
        else:
            raw = raw_data or {}

        # Extraire les token IDs
        token_ids = raw.get("clobTokenIds", [])
        if isinstance(token_ids, str):
            try:
                token_ids = json.loads(token_ids)
            except Exception:
                token_ids = []

        if not token_ids:
            return None

        token_id = token_ids[0]

        try:
            resp = await self._http.get(
                f"{CLOB_API_URL}/trades",
                params={"market": token_id, "limit": 50},
                timeout=10.0,
            )
            if resp.status_code != 200:
                return None
            trades_raw = resp.json()
        except Exception as e:
            logger.debug(f"SmartMoney trades fetch erreur: {e}")
            return None

        # Normaliser la réponse (liste ou dict avec "data")
        if isinstance(trades_raw, dict):
            trades_raw = trades_raw.get("data", [])
        if not isinstance(trades_raw, list) or not trades_raw:
            return None

        # Filtrer par taille et fenêtre temporelle
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=LOOKBACK_HOURS)
        large_trades: list[dict] = []

        for trade in trades_raw:
            try:
                size_shares = float(trade.get("size", 0))
                price = float(trade.get("price", 0.5))
                size_usd = size_shares * price
            except (ValueError, TypeError):
                continue

            if size_usd < MIN_TRADE_SIZE_USD:
                continue

            # Vérification temporelle
            ts_raw = trade.get("timestamp") or trade.get("created_at") or trade.get("matchTime", "")
            if ts_raw:
                try:
                    ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    if ts < cutoff:
                        continue
                except Exception:
                    pass

            # Déterminer la direction
            side_raw = str(trade.get("side", "")).upper()
            outcome = str(trade.get("outcome", "")).upper()
            if side_raw in ("BUY", "YES") or outcome == "YES":
                side = "YES"
            elif side_raw in ("SELL", "NO") or outcome == "NO":
                side = "NO"
            else:
                # Déduire depuis le prix : > 50¢ = probable YES
                side = "YES" if price > 0.5 else "NO"

            wallet = (
                trade.get("maker_address") or
                trade.get("transactorAddress") or
                trade.get("owner", "")
            )

            large_trades.append({
                "wallet": str(wallet),
                "size_usd": size_usd,
                "side": side,
                "price": price,
            })

        if not large_trades:
            return None

        # Grouper par direction
        yes_trades = [t for t in large_trades if t["side"] == "YES"]
        no_trades  = [t for t in large_trades if t["side"] == "NO"]

        yes_wallets = len(set(t["wallet"] for t in yes_trades if t["wallet"]))
        no_wallets  = len(set(t["wallet"] for t in no_trades  if t["wallet"]))
        yes_volume  = sum(t["size_usd"] for t in yes_trades)
        no_volume   = sum(t["size_usd"] for t in no_trades)

        # Direction dominante
        if yes_wallets >= MIN_WALLETS_ALIGNED and yes_wallets >= no_wallets:
            direction = "YES"
            dominant_wallets = yes_wallets
            dominant_volume  = yes_volume
            opposite_volume  = no_volume
        elif no_wallets >= MIN_WALLETS_ALIGNED and no_wallets > yes_wallets:
            direction = "NO"
            dominant_wallets = no_wallets
            dominant_volume  = no_volume
            opposite_volume  = yes_volume
        else:
            return None

        total_volume = dominant_volume + opposite_volume
        if total_volume <= 0:
            return None

        volume_ratio = dominant_volume / total_volume  # 0.5 → 1.0

        yes_price = float(market.get("yes_price", 0.5))

        # Probabilité estimée : légère correction vers la direction des smart money
        if direction == "YES":
            predicted_prob = min(yes_price + 0.06 + (volume_ratio - 0.5) * 0.25, 0.90)
            edge = predicted_prob - yes_price
        else:
            predicted_prob = max(yes_price - 0.06 - (volume_ratio - 0.5) * 0.25, 0.10)
            edge = yes_price - predicted_prob

        if abs(edge) < 0.05:
            return None

        confidence = min(
            BASE_CONFIDENCE
            + dominant_wallets * 0.025
            + (volume_ratio - 0.5) * 0.10,
            0.84,
        )

        reasoning = (
            f"{dominant_wallets} gros trader(s) ont misé "
            f"${dominant_volume:,.0f} en {direction} ces {LOOKBACK_HOURS}h "
            f"(vs ${opposite_volume:,.0f} en sens inverse). "
            f"Concentration de smart money détectée — signal de copy trading."
        )

        logger.info(
            f"SMART MONEY: {dominant_wallets} wallets → {direction} "
            f"${dominant_volume:.0f} | {market.get('question', '')[:50]}"
        )

        return {
            "market_id": market.get("id", ""),
            "question": market.get("question", ""),
            "signal_type": "SMART_MONEY",
            "direction": direction,
            "confidence": round(confidence, 4),
            "edge": round(edge, 4),
            "predicted_prob": round(predicted_prob, 4),
            "market_price": round(yes_price, 4),
            "sentiment_score": 0.0,
            "source": f"Smart Money ({dominant_wallets} wallets, ${dominant_volume:.0f})",
            "texts_count": dominant_wallets,
            "market_url": market.get("market_url", ""),
            "urgency_bonus": market.get("urgency_bonus", 0),
            "category": market.get("category", "other"),
            "llm_reasoning": reasoning,
            "llm_valid": True,
        }

    def stop(self):
        self._running = False
        logger.info("Agent 15 (Smart Money) arrêté")
