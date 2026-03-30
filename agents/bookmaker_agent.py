"""
PolyPoly — Agent 13 : Comparaison Cotes Bookmaker
Compare les probabilités Polymarket avec les cotes professionnelles
Vegas/Bet365/DraftKings via The Odds API (tier gratuit).
Les bookmakers ont des modèles calibrés sur des décennies — une divergence
avec Polymarket est un signal très fort.
"""

import asyncio
import re
from typing import Optional
from loguru import logger
import httpx

from config import ODDS_API_KEY
from utils.database import Database

ODDS_API_BASE = "https://api.the-odds-api.com/v4"
SCAN_INTERVAL_SEC = 600      # Toutes les 10 minutes (économiser les requêtes gratuites)
MIN_DIVERGENCE = 0.10        # 10% de divergence minimum avec les bookmakers

# Sports couverts par The Odds API (gratuit) → Sports Polymarket
SPORTS_MAP = {
    "basketball_nba": ["nba", "basketball", "lakers", "celtics", "knicks", "bulls"],
    "americanfootball_nfl": ["nfl", "football", "super bowl", "patriots", "chiefs"],
    "baseball_mlb": ["mlb", "baseball", "yankees", "dodgers", "mets"],
    "soccer_epl": ["premier league", "epl", "arsenal", "chelsea", "liverpool", "manchester"],
    "soccer_uefa_champs_league": ["champions league", "ucl", "real madrid", "barcelona", "psg"],
    "mma_mixed_martial_arts": ["ufc", "mma", "bellator"],
    "basketball_ncaab": ["ncaa", "ncaab", "college basketball", "march madness"],
    "americanfootball_ncaaf": ["ncaaf", "college football"],
    "tennis_atp": ["atp", "djokovic", "alcaraz", "sinner", "nadal", "federer"],
    "tennis_wta": ["wta", "swiatek", "sabalenka", "gauff"],
}


class BookmakerAgent:
    """
    Agent 13 — Comparaison avec les cotes bookmaker professionnelles.

    Pour chaque marché sportif Polymarket :
    1. Identifie le sport et les équipes/joueurs
    2. Récupère les cotes Vegas/Bet365/Pinnacle via The Odds API
    3. Convertit les cotes en probabilités implicites
    4. Compare avec le prix Polymarket
    5. Si divergence > 10% → signal BOOKMAKER (très haute fiabilité)

    Note : Requiert ODDS_API_KEY dans .env (gratuit sur the-odds-api.com)
    """

    def __init__(self, db: Database, telegram):
        self.db = db
        self.telegram = telegram
        self._http = httpx.AsyncClient(timeout=15.0)
        self._running = False
        self._enabled = bool(ODDS_API_KEY)
        self._requests_used = 0

    async def run_forever(self):
        if not self._enabled:
            logger.warning(
                "Agent 13 (Bookmaker) désactivé — ODDS_API_KEY manquant dans .env\n"
                "Inscription gratuite sur : https://the-odds-api.com"
            )
            return
        self._running = True
        logger.info("Agent 13 (Bookmaker Odds) démarré")
        while self._running:
            try:
                await self._scan_cycle()
            except Exception as e:
                logger.warning(f"Bookmaker agent erreur: {e}")
            await asyncio.sleep(SCAN_INTERVAL_SEC)

    async def _scan_cycle(self):
        """Compare les marchés sportifs Polymarket avec les cotes bookmaker."""
        markets = await self.db.get_active_markets(limit=100)
        sports_markets = [
            m for m in markets
            if m.get("category") == "sports"
        ]

        if not sports_markets:
            return

        signals_found = 0
        for sport_key, keywords in SPORTS_MAP.items():
            # Trouver les marchés Polymarket pour ce sport
            relevant = [
                m for m in sports_markets
                if any(kw in m.get("question", "").lower() for kw in keywords)
            ]
            if not relevant:
                continue

            # Récupérer les cotes pour ce sport
            odds_data = await self._fetch_odds(sport_key)
            if not odds_data:
                continue

            for market in relevant:
                signal = await self._compare_with_bookmakers(market, odds_data)
                if signal:
                    await self.db.save_signal(signal)
                    signals_found += 1
                    if signal["confidence"] >= 0.72:
                        await self.telegram.notify_opportunity(signal)

            await asyncio.sleep(2)  # Rate limit

        if signals_found:
            logger.info(f"Bookmaker: {signals_found} divergences vs cotes pro détectées")

    async def _fetch_odds(self, sport: str) -> list[dict]:
        """Récupère les cotes actuelles pour un sport donné."""
        try:
            url = f"{ODDS_API_BASE}/sports/{sport}/odds/"
            params = {
                "apiKey": ODDS_API_KEY,
                "regions": "us,eu",
                "markets": "h2h",         # Head-to-head (moneyline)
                "oddsFormat": "decimal",
            }
            resp = await self._http.get(url, params=params, timeout=10.0)
            if resp.status_code == 401:
                logger.warning("Bookmaker: API key invalide")
                self._enabled = False
                return []
            if resp.status_code == 429:
                logger.warning("Bookmaker: quota API dépassé")
                return []
            if resp.status_code != 200:
                return []

            # Compter les requêtes restantes
            remaining = resp.headers.get("x-requests-remaining", "?")
            self._requests_used += 1
            if self._requests_used % 10 == 0:
                logger.info(f"Bookmaker: {remaining} requêtes API restantes ce mois")

            return resp.json()
        except Exception as e:
            logger.debug(f"Bookmaker fetch erreur: {e}")
            return []

    async def _compare_with_bookmakers(
        self, market: dict, odds_data: list[dict]
    ) -> Optional[dict]:
        """Compare un marché Polymarket avec les cotes bookmaker."""
        question = market.get("question", "").lower()
        yes_price = market.get("yes_price", 0.5)

        # Trouver un match dans les données bookmaker
        best_match = None
        best_score = 0

        q_words = set(re.findall(r'\b\w{3,}\b', question))

        for event in odds_data:
            home = (event.get("home_team") or "").lower()
            away = (event.get("away_team") or "").lower()
            event_text = f"{home} {away}"
            e_words = set(re.findall(r'\b\w{3,}\b', event_text))
            score = len(q_words & e_words)
            if score > best_score and score >= 2:
                best_score = score
                best_match = event

        if not best_match:
            return None

        # Extraire la meilleure cote disponible (Pinnacle > Draftkings > Bet365)
        bookmaker_prob = self._extract_best_prob(best_match, question)
        if bookmaker_prob is None:
            return None

        divergence = bookmaker_prob - yes_price
        abs_div = abs(divergence)

        if abs_div < MIN_DIVERGENCE:
            return None

        direction = "YES" if divergence > 0 else "NO"
        # Confiance très haute car les bookmakers sont très bien calibrés
        confidence = min(0.70 + abs_div * 2.0, 0.92)

        bookmakers_names = [b.get("title", "?") for b in best_match.get("bookmakers", [])[:3]]

        logger.info(
            f"BOOKMAKER DIVERGENCE: Poly={yes_price:.0%} Pro={bookmaker_prob:.0%} "
            f"(+{abs_div:.0%}) | {market.get('question', '')[:55]}"
        )

        return {
            "market_id": market["id"],
            "question": market.get("question", ""),
            "signal_type": "BOOKMAKER",
            "direction": direction,
            "confidence": round(confidence, 4),
            "edge": round(divergence, 4),
            "predicted_prob": round(bookmaker_prob, 4),
            "market_price": round(yes_price, 4),
            "sentiment_score": 0.0,
            "source": f"Bookmakers pro ({', '.join(bookmakers_names[:2])})",
            "texts_count": len(best_match.get("bookmakers", [])),
            "market_url": market.get("market_url", ""),
            "urgency_bonus": market.get("urgency_bonus", 0),
            "category": "sports",
            "llm_reasoning": (
                f"Les bookmakers professionnels ({', '.join(bookmakers_names[:2])}) estiment "
                f"la probabilité à {bookmaker_prob:.0%} contre {yes_price:.0%} sur Polymarket. "
                f"Divergence de {abs_div:.0%} — les bookmakers ont des modèles calibrés sur des décennies."
            ),
            "llm_valid": True,
        }

    @staticmethod
    def _extract_best_prob(event: dict, question: str) -> Optional[float]:
        """Extrait la probabilité implicite de la meilleure cote disponible."""
        # Ordre de préférence des bookmakers (du plus précis au moins précis)
        preferred = ["Pinnacle", "DraftKings", "FanDuel", "BetMGM", "Bet365", "Bovada"]

        bookmakers = event.get("bookmakers", [])
        if not bookmakers:
            return None

        # Trier par préférence
        def book_rank(b):
            title = b.get("title", "")
            for i, p in enumerate(preferred):
                if p.lower() in title.lower():
                    return i
            return 99

        bookmakers_sorted = sorted(bookmakers, key=book_rank)

        for bookmaker in bookmakers_sorted:
            for market in bookmaker.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                outcomes = market.get("outcomes", [])
                if len(outcomes) < 2:
                    continue

                # Matcher l'outcome avec la question Polymarket
                q_lower = question.lower()
                for outcome in outcomes:
                    name = outcome.get("name", "").lower()
                    name_words = set(re.findall(r'\b\w{3,}\b', name))
                    q_words = set(re.findall(r'\b\w{3,}\b', q_lower))
                    if len(name_words & q_words) >= 1:
                        decimal_odds = float(outcome.get("price", 2.0))
                        if decimal_odds > 1.0:
                            # Convertir cote décimale en probabilité implicite
                            return round(1.0 / decimal_odds, 4)

        return None

    def stop(self):
        self._running = False
        logger.info("Agent 13 (Bookmaker) arrêté")
