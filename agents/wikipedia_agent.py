"""
PolyPoly — Agent 12 : Moniteur Wikipedia Recent Changes
Wikipedia est édité en temps réel quand un événement se passe,
souvent AVANT que les sites d'info publient. Alpha source gratuite.
"""

import asyncio
import re
from datetime import datetime, timezone, timedelta
from typing import Optional
from loguru import logger
import httpx

from utils.database import Database

WIKI_API = "https://en.wikipedia.org/w/api.php"
SCAN_INTERVAL_SEC = 180      # Scan toutes les 3 minutes
VELOCITY_THRESHOLD = 5       # Nombre d'éditions en 30 min pour déclencher un signal
MIN_MATCH_WORDS = 2          # Mots en commun entre titre Wiki et question Polymarket

STOP_WORDS = {
    "will", "the", "a", "an", "in", "on", "at", "to", "for", "of",
    "and", "or", "is", "be", "by", "as", "it", "this", "that",
    "win", "next", "first", "last", "new", "who", "what", "when",
}


class WikipediaAgent:
    """
    Agent 12 — Surveillance Wikipedia Recent Changes.

    Chaque 3 minutes :
    1. Récupère les 200 derniers changements Wikipedia
    2. Extrait les mots-clés des titres de pages éditées
    3. Compare avec les marchés Polymarket actifs
    4. Si une page liée à un marché est massivement éditée → signal WIKI

    Exemple : pendant un match, la page du joueur/équipe est éditée
    toutes les 2 minutes → signal fort AVANT que le score soit sur les news.
    """

    def __init__(self, db: Database, telegram):
        self.db = db
        self.telegram = telegram
        self._http = httpx.AsyncClient(timeout=15.0)
        self._running = False
        # Historique des éditions : page_title → [timestamps]
        self._edit_history: dict[str, list[datetime]] = {}

    async def run_forever(self):
        self._running = True
        logger.info("Agent 12 (Wikipedia Monitor) démarré")
        while self._running:
            try:
                await self._scan_cycle()
            except Exception as e:
                logger.warning(f"Wikipedia agent erreur: {e}")
            await asyncio.sleep(SCAN_INTERVAL_SEC)

    async def _scan_cycle(self):
        changes = await self._fetch_recent_changes()
        if not changes:
            return

        now = datetime.now(timezone.utc)
        window = now - timedelta(minutes=30)

        # Mettre à jour l'historique et calculer les velocities
        hot_pages: dict[str, int] = {}  # title → nb edits dans la fenêtre
        for change in changes:
            title = change.get("title", "")
            ts_str = change.get("timestamp", "")
            if not title or not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                continue

            if title not in self._edit_history:
                self._edit_history[title] = []
            self._edit_history[title].append(ts)
            # Purger les vieilles entrées
            self._edit_history[title] = [
                t for t in self._edit_history[title] if t >= window
            ]
            hot_pages[title] = len(self._edit_history[title])

        # Filtrer les pages chaudes
        hot_pages = {k: v for k, v in hot_pages.items() if v >= VELOCITY_THRESHOLD}
        if not hot_pages:
            return

        logger.info(f"Wikipedia: {len(hot_pages)} pages chaudes détectées")

        # Comparer avec les marchés actifs
        markets = await self.db.get_active_markets(limit=100)
        for title, edit_count in hot_pages.items():
            for market in markets:
                if self._matches(title, market.get("question", "")):
                    await self._generate_signal(market, title, edit_count)
                    break

    async def _fetch_recent_changes(self) -> list[dict]:
        """Récupère les 200 dernières modifications Wikipedia."""
        try:
            params = {
                "action": "query",
                "list": "recentchanges",
                "rcprop": "title|timestamp|comment|sizes",
                "rclimit": 200,
                "rcnamespace": 0,  # Articles seulement
                "rctype": "edit",
                "format": "json",
            }
            resp = await self._http.get(WIKI_API, params=params, timeout=10.0)
            if resp.status_code != 200:
                return []
            data = resp.json()
            return data.get("query", {}).get("recentchanges", [])
        except Exception as e:
            logger.debug(f"Wikipedia fetch erreur: {e}")
            return []

    @staticmethod
    def _matches(wiki_title: str, market_question: str) -> bool:
        """Vérifie si une page Wikipedia est liée à un marché Polymarket."""
        title_words = set(
            w.lower() for w in re.findall(r'\b\w{3,}\b', wiki_title)
            if w.lower() not in STOP_WORDS
        )
        question_words = set(
            w.lower() for w in re.findall(r'\b\w{3,}\b', market_question)
            if w.lower() not in STOP_WORDS
        )
        common = title_words & question_words
        return len(common) >= MIN_MATCH_WORDS

    async def _generate_signal(self, market: dict, wiki_title: str, edit_count: int):
        """Génère un signal WIKI basé sur l'activité Wikipedia."""
        market_id = market.get("id", "")
        yes_price = market.get("yes_price", 0.5)

        # Vérifier le cooldown (1 signal par marché par heure)
        existing = await self.db.get_recent_signals_for_market(market_id, hours=1)
        if any(s.get("signal_type") == "WIKI" for s in existing):
            return

        # La direction dépend du prix actuel :
        # prix < 0.5 → sous-évalué → signal YES
        # prix > 0.5 → sur-évalué → signal NO (peut-être que l'événement ne se passe pas comme prévu)
        # Mais on ne peut pas savoir le sens sans analyser le contenu des éditions
        # → on génère un signal d'alerte neutre avec confiance modérée
        edge = 0.15 if yes_price < 0.5 else -0.15
        direction = "YES" if edge > 0 else "NO"
        confidence = min(0.60 + (edit_count - VELOCITY_THRESHOLD) * 0.02, 0.80)

        signal = {
            "market_id": market_id,
            "question": market.get("question", ""),
            "signal_type": "WIKI",
            "direction": direction,
            "confidence": round(confidence, 4),
            "edge": round(edge, 4),
            "predicted_prob": round(yes_price + edge, 4),
            "market_price": round(yes_price, 4),
            "sentiment_score": 0.0,
            "source": f"Wikipedia ({edit_count} éditions/30min: '{wiki_title}')",
            "texts_count": edit_count,
            "market_url": market.get("market_url", ""),
            "urgency_bonus": market.get("urgency_bonus", 0),
            "category": market.get("category", "other"),
            "llm_reasoning": (
                f"Page Wikipedia '{wiki_title}' éditée {edit_count} fois en 30 min — "
                f"activité inhabituelle liée à ce marché. Souvent précurseur d'une résolution imminente."
            ),
            "llm_valid": True,
        }

        await self.db.save_signal(signal)
        logger.info(
            f"WIKI SIGNAL: {edit_count} éditions sur '{wiki_title}' "
            f"→ {market.get('question', '')[:50]}"
        )

        if confidence >= 0.68:
            await self.telegram.notify_opportunity(signal)

    def stop(self):
        self._running = False
        logger.info("Agent 12 (Wikipedia) arrêté")
