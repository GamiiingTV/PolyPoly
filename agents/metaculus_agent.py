"""
PolyPoly — Agent 9 : Consensus Metaculus
Cross-référence les marchés Polymarket avec les prédictions d'experts Metaculus.
API publique, pas de clé requise.

Si Metaculus (experts calibrés) dit 65% et Polymarket dit 30% → edge réel de 35%.
"""

import asyncio
import re
import httpx
from datetime import datetime
from typing import Optional
from loguru import logger

METACULUS_API = "https://www.metaculus.com/api2/questions/"
MANIFOLD_API = "https://api.manifold.markets/v0/search-markets"

# Seuil d'écart pour générer un signal Metaculus
MIN_METACULUS_EDGE = 0.12  # 12% d'écart minimum pour être pertinent


class MetaculusAgent:
    """
    Agent 9 — Consensus d'experts Metaculus + Manifold.

    Pour chaque signal fort, cherche la même question sur Metaculus.
    Si les experts disent une probabilité très différente du marché Polymarket,
    c'est un signal fort supplémentaire (ou un avertissement).
    """

    def __init__(self):
        self._http = httpx.AsyncClient(
            timeout=10.0,
            headers={"User-Agent": "PolyPolyBot/2.0 (prediction market research)"},
        )
        self._cache: dict[str, Optional[dict]] = {}

    async def get_expert_consensus(self, market: dict) -> Optional[dict]:
        """
        Cherche une question correspondante sur Metaculus.
        Retourne les données de consensus si trouvées.
        """
        market_id = market.get("id", "")
        if market_id in self._cache:
            return self._cache[market_id]

        question = market.get("question", "")
        if not question:
            return None

        result = await self._search_metaculus(question)
        if not result:
            result = await self._search_manifold(question, market)

        self._cache[market_id] = result
        return result

    async def _search_metaculus(self, question: str) -> Optional[dict]:
        """Cherche sur Metaculus."""
        stop = {"will", "the", "a", "an", "in", "on", "at", "to", "for",
                "of", "and", "or", "is", "be", "by", "2026", "2025", "march",
                "april", "may", "june", "hit", "dip", "win", "end"}
        words = [
            w for w in re.findall(r'\b[a-z]{4,}\b', question.lower())
            if w not in stop
        ][:4]

        if len(words) < 2:
            return None

        query = " ".join(words)
        try:
            resp = await self._http.get(
                METACULUS_API,
                params={"search": query, "status": "open", "limit": 5},
            )
            if resp.status_code != 200:
                return None

            results = resp.json().get("results", [])
            best, best_score = None, 0

            for q in results:
                title = q.get("title", "").lower()
                score = sum(1 for w in words if w in title)
                if score > best_score and score >= 2:
                    best_score = score
                    best = q

            if not best:
                return None

            # Extraire la probabilité médiane
            cp = best.get("community_prediction", {})
            prob = None
            if isinstance(cp, dict):
                prob = cp.get("full", {}).get("q2")

            if prob is None:
                return None

            return {
                "source": "Metaculus",
                "expert_prob": float(prob),
                "title": best.get("title", "")[:80],
                "url": f"https://www.metaculus.com/questions/{best.get('id')}/",
                "match_score": best_score,
                "forecasters": best.get("number_of_forecasters", 0),
            }
        except Exception as e:
            logger.debug(f"Metaculus search erreur: {e}")
            return None

    async def _search_manifold(self, question: str, market: dict) -> Optional[dict]:
        """Cherche sur Manifold Markets comme fallback."""
        stop = {"will", "the", "a", "an", "in", "on", "at", "to", "for",
                "of", "and", "or", "is", "be", "by"}
        words = [
            w for w in re.findall(r'\b[a-z]{4,}\b', question.lower())
            if w not in stop
        ][:3]

        if len(words) < 2:
            return None

        try:
            resp = await self._http.get(
                MANIFOLD_API,
                params={"terms": " ".join(words), "limit": 5, "filter": "open"},
            )
            if resp.status_code != 200:
                return None

            results = resp.json()
            if not isinstance(results, list):
                return None

            best, best_score = None, 0
            for m in results:
                title = m.get("question", "").lower()
                score = sum(1 for w in words if w in title)
                if score > best_score and score >= 2:
                    best_score = score
                    best = m

            if not best:
                return None

            prob = best.get("probability")
            if prob is None:
                return None

            return {
                "source": "Manifold",
                "expert_prob": float(prob),
                "title": best.get("question", "")[:80],
                "url": best.get("url", ""),
                "match_score": best_score,
                "forecasters": best.get("uniqueBettorCount", 0),
            }
        except Exception as e:
            logger.debug(f"Manifold search erreur: {e}")
            return None

    def compute_edge_vs_polymarket(
        self, consensus: dict, polymarket_yes_price: float
    ) -> float:
        """
        Calcule l'écart entre le consensus expert et le prix Polymarket.
        Positif = experts plus optimistes que Polymarket (signal YES).
        """
        return consensus["expert_prob"] - polymarket_yes_price

    def stop(self):
        logger.info("Agent 9 (Metaculus) arrêté")
