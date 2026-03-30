"""
PolyPoly — Agent 11 : Arbitrage Inter-Plateformes
Compare Polymarket vs Manifold en temps réel pour détecter les divergences.
Quand Manifold dit 60% et Polymarket dit 35% → signal quasi-certain.
"""

import asyncio
import re
from typing import Optional
from loguru import logger
import httpx

from utils.database import Database

MANIFOLD_SEARCH_URL = "https://api.manifold.markets/v0/search-markets"
SCAN_INTERVAL_SEC = 300        # Scan toutes les 5 minutes
MIN_DIVERGENCE = 0.12          # 12% d'écart minimum pour générer un signal
MATCH_WORDS_MIN = 2            # Au moins 2 mots en commun pour matcher les marchés

STOP_WORDS = {
    "will", "the", "a", "an", "in", "on", "at", "to", "for", "of",
    "and", "or", "is", "be", "by", "as", "it", "this", "that", "be",
    "win", "next", "first", "last", "new", "any", "all", "more",
}


class CrossPlatformAgent:
    """
    Agent 11 — Arbitrage inter-plateformes.

    Pour chaque marché Polymarket actif :
    - Cherche un marché équivalent sur Manifold Markets (API gratuite)
    - Compare les probabilités implicites
    - Génère un signal ARBITRAGE si divergence > 12%

    Exemple : Polymarket dit 30% pour "Trump élu", Manifold dit 55%
    → Signal fort YES avec edge +25%
    """

    def __init__(self, db: Database, telegram):
        self.db = db
        self.telegram = telegram
        self._http = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
        self._running = False
        self._cache: dict[str, float] = {}   # market_id → manifold_prob (cache 30min)
        self._cache_ts: dict[str, float] = {}

    async def run_forever(self):
        self._running = True
        logger.info("Agent 11 (Cross-Platform Arbitrage) démarré")
        while self._running:
            try:
                await self._scan_cycle()
            except Exception as e:
                logger.warning(f"CrossPlatform erreur: {e}")
            await asyncio.sleep(SCAN_INTERVAL_SEC)

    async def _scan_cycle(self):
        import time
        markets = await self.db.get_active_markets(limit=60)
        signals_found = 0
        now = time.time()

        for market in markets:
            market_id = market.get("id", "")
            # Cache 30 minutes pour éviter de surcharger Manifold
            if market_id in self._cache_ts and (now - self._cache_ts[market_id]) < 1800:
                continue

            signal = await self._check_divergence(market)
            self._cache_ts[market_id] = now

            if signal:
                await self.db.save_signal(signal)
                signals_found += 1
                if signal["confidence"] >= 0.68:
                    await self.telegram.notify_opportunity(signal)

            await asyncio.sleep(1.5)  # Respecter le rate limit Manifold

        if signals_found:
            logger.info(f"CrossPlatform: {signals_found} divergences détectées")

    async def _check_divergence(self, market: dict) -> Optional[dict]:
        question = market.get("question", "")
        yes_price = market.get("yes_price", 0.5)

        manifold = await self._search_manifold(question)
        if not manifold:
            return None

        manifold_prob = manifold["probability"]
        divergence = manifold_prob - yes_price
        abs_div = abs(divergence)

        if abs_div < MIN_DIVERGENCE:
            return None

        traders = manifold["traders"]
        direction = "YES" if divergence > 0 else "NO"

        # Confiance pondérée par le nombre de traders Manifold :
        # Avec 18 traders, Manifold est peu fiable vs Polymarket.
        # Avec 200+ traders, la divergence est plus crédible.
        trader_weight = min(traders / 100, 1.0)   # 0.0 → 1.0 selon le volume Manifold

        # Si Polymarket a un prix < 15¢ ou > 85¢, ses traders ont probablement
        # plus d'info sur un marché factuel (tweet count, score sportif, etc.)
        polymarket_informed_bonus = 0.0
        if yes_price < 0.15 or yes_price > 0.85:
            polymarket_informed_bonus = -0.10  # Pénalité : Polymarket probablement correct

        # Si résolution dans < 48h, Polymarket est généralement mieux informé
        urgency = market.get("urgency_bonus", 0)
        if urgency >= 0.25:
            polymarket_informed_bonus -= 0.08  # Encore plus de pénalité si résolution imminente

        base_confidence = 0.62 + abs_div * 1.8
        confidence = min(
            base_confidence * (0.5 + trader_weight * 0.5) + polymarket_informed_bonus,
            0.88
        )

        if confidence < 0.60:
            logger.debug(
                f"Cross-platform rejeté (confiance trop basse {confidence:.0%}): "
                f"{question[:50]}"
            )
            return None

        logger.info(
            f"DIVERGENCE INTER-PLATEFORME: Poly={yes_price:.0%} "
            f"Manifold={manifold_prob:.0%} (+{abs_div:.0%}) | {question[:55]}"
        )

        reasoning = (
            f"Manifold ({manifold['traders']} traders) évalue à {manifold_prob:.0%} "
            f"alors que Polymarket affiche {yes_price:.0%}. "
            f"Divergence de {abs_div:.0%} — probable inefficience de marché à exploiter."
        )

        return {
            "market_id": market["id"],
            "question": question,
            "signal_type": "ARBITRAGE",
            "direction": direction,
            "confidence": round(confidence, 4),
            "edge": round(divergence, 4),
            "predicted_prob": round(manifold_prob, 4),
            "market_price": round(yes_price, 4),
            "sentiment_score": 0.0,
            "source": f"Arbitrage Manifold ({manifold_prob:.0%} vs Poly {yes_price:.0%})",
            "texts_count": manifold["traders"],
            "market_url": market.get("market_url", ""),
            "urgency_bonus": market.get("urgency_bonus", 0),
            "category": market.get("category", "other"),
            "llm_reasoning": reasoning,
            "llm_valid": True,
            "cross_platform_source": "Manifold",
            "cross_platform_prob": manifold_prob,
            "cross_platform_url": manifold.get("url", ""),
        }

    async def _search_manifold(self, question: str) -> Optional[dict]:
        """Cherche un marché BINARY correspondant sur Manifold Markets."""
        words = [
            w.lower() for w in re.findall(r'\b\w{3,}\b', question)
            if w.lower() not in STOP_WORDS
        ][:5]

        if len(words) < 2:
            return None

        term = " ".join(words[:3])

        try:
            resp = await self._http.get(
                MANIFOLD_SEARCH_URL,
                params={"term": term, "limit": 12, "filter": "open"},
                timeout=10.0,
            )
            if resp.status_code != 200:
                return None

            results = resp.json()
            if not isinstance(results, list) or not results:
                return None

            best = None
            best_score = 0

            for m in results:
                if m.get("outcomeType") != "BINARY":
                    continue
                if m.get("isResolved"):
                    continue
                m_q = m.get("question", "").lower()
                score = sum(1 for w in words if w in m_q)
                if score > best_score and score >= MATCH_WORDS_MIN:
                    best_score = score
                    best = m

            if not best:
                return None

            prob = best.get("probability", 0.5)
            traders = best.get("uniqueBettorCount", 0)
            # Ignorer les marchés Manifold avec peu de traders (données peu fiables)
            if traders < 25:
                return None

            return {
                "probability": float(prob),
                "title": best.get("question", ""),
                "traders": traders,
                "url": f"https://manifold.markets/{best.get('creatorUsername', '')}/{best.get('slug', '')}",
            }

        except Exception as e:
            logger.debug(f"Manifold API erreur: {e}")
            return None

    def stop(self):
        self._running = False
        logger.info("Agent 11 (Cross-Platform) arrêté")
