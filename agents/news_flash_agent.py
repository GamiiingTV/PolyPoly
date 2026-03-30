"""
PolyPoly — Agent 14 : News Flash
Envoie des alertes Telegram informatives (pas des trades) quand des
breaking news (<3h) correspondent à des marchés Polymarket à fort volume.
"""

import asyncio
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from typing import Optional
from loguru import logger
import httpx

from utils.database import Database
from config import RSS_FEEDS

SCAN_INTERVAL_SEC = 600       # toutes les 10 minutes
MAX_NEWS_AGE_HOURS = 3        # articles < 3h
MIN_VOLUME_USD = 3000         # marchés > $3k/24h volume
MIN_MATCH_WORDS = 2           # mots-clés communs minimum
MAX_FLASHES_PER_CYCLE = 3     # max 3 alertes par cycle
FLASH_COOLDOWN_HOURS = 4      # même article-marché → 4h entre alertes

STOP_WORDS = {
    "will", "the", "a", "an", "in", "on", "at", "to", "for", "of",
    "and", "or", "is", "be", "by", "as", "it", "this", "that",
    "has", "have", "had", "are", "was", "were", "been", "being",
    "says", "said", "new", "first", "after", "before", "over",
    "from", "with", "his", "her", "its", "not", "but", "how",
}


class NewsFlashAgent:
    """
    Agent 14 — Flash Info Telegram.

    Surveille les flux RSS toutes les 10 minutes, identifie les articles récents
    (<3h) et les corrèle avec les marchés Polymarket à fort volume.
    Envoie une alerte Telegram 📰 (informative, pas un signal de trade).
    """

    def __init__(self, db: Database, telegram):
        self.db = db
        self.telegram = telegram
        self._http = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
        self._running = False
        # (article_url + market_id) → heure du dernier flash
        self._seen_flash: dict[str, datetime] = {}

    async def run_forever(self):
        self._running = True
        logger.info("Agent 14 (News Flash) démarré")
        while self._running:
            try:
                await self._scan_cycle()
            except Exception as e:
                logger.warning(f"NewsFlash erreur: {e}")
            await asyncio.sleep(SCAN_INTERVAL_SEC)

    async def _scan_cycle(self):
        articles = await self._fetch_recent_articles()
        if not articles:
            return

        markets = await self.db.get_active_markets(limit=200)
        high_volume = [m for m in markets if m.get("volume_24h", 0) >= MIN_VOLUME_USD]
        if not high_volume:
            return

        flashes_sent = 0
        now = datetime.now(timezone.utc)

        for article in articles:
            if flashes_sent >= MAX_FLASHES_PER_CYCLE:
                break

            best_market, score = self._match_to_market(article, high_volume)
            if not best_market or score < MIN_MATCH_WORDS:
                continue

            cache_key = f"{article.get('url', '')[:80]}|{best_market.get('id', '')}"
            last_seen = self._seen_flash.get(cache_key)
            if last_seen and (now - last_seen).total_seconds() < FLASH_COOLDOWN_HOURS * 3600:
                continue

            self._seen_flash[cache_key] = now
            await self.telegram.notify_news_flash(article, best_market)
            flashes_sent += 1

            logger.info(
                f"NewsFlash: [{score} mots] {article.get('title', '')[:60]} "
                f"→ {best_market.get('question', '')[:50]}"
            )

        # Nettoyer le cache (>12h)
        cutoff = now - timedelta(hours=12)
        self._seen_flash = {k: v for k, v in self._seen_flash.items() if v > cutoff}

        if flashes_sent:
            logger.info(f"NewsFlash: {flashes_sent} flash(es) envoyé(s)")

    async def _fetch_recent_articles(self) -> list[dict]:
        """Récupère les articles récents depuis les flux RSS configurés."""
        articles = []
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=MAX_NEWS_AGE_HOURS)

        # Limiter à 10 feeds pour performance
        for feed_url in RSS_FEEDS[:10]:
            try:
                resp = await self._http.get(feed_url, timeout=8.0)
                if resp.status_code != 200:
                    continue

                root = ET.fromstring(resp.text)
                channel = root.find("channel")
                items = []

                if channel is not None:
                    items = channel.findall("item")
                else:
                    # Format Atom
                    ns = "{http://www.w3.org/2005/Atom}"
                    items = root.findall(f"{ns}entry")

                for item in items[:15]:
                    ns_atom = "{http://www.w3.org/2005/Atom}"
                    title_elem = (
                        item.find("title") or
                        item.find(f"{ns_atom}title")
                    )
                    link_elem = (
                        item.find("link") or
                        item.find(f"{ns_atom}link")
                    )
                    date_elem = (
                        item.find("pubDate") or
                        item.find(f"{ns_atom}published") or
                        item.find(f"{ns_atom}updated")
                    )

                    if title_elem is None:
                        continue

                    title = (title_elem.text or "").strip()
                    if not title:
                        continue

                    link = ""
                    if link_elem is not None:
                        link = (link_elem.text or link_elem.get("href", "")).strip()

                    pub_date = None
                    if date_elem is not None and date_elem.text:
                        raw_date = date_elem.text.strip()
                        try:
                            pub_date = parsedate_to_datetime(raw_date)
                        except Exception:
                            try:
                                pub_date = datetime.fromisoformat(
                                    raw_date.replace("Z", "+00:00")
                                )
                            except Exception:
                                pass

                    if pub_date is None:
                        continue
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                    if pub_date < cutoff:
                        continue

                    domain = feed_url.split("/")[2] if "/" in feed_url else feed_url
                    articles.append({
                        "title": title,
                        "url": link,
                        "pub_date": pub_date,
                        "source": domain,
                    })

            except Exception as e:
                logger.debug(f"NewsFlash RSS erreur ({feed_url[:40]}): {e}")

        # Trier par date (plus récent d'abord)
        articles.sort(
            key=lambda x: x.get("pub_date", datetime.min.replace(tzinfo=timezone.utc)),
            reverse=True,
        )
        return articles

    def _match_to_market(
        self, article: dict, markets: list[dict]
    ) -> tuple[Optional[dict], int]:
        """
        Trouve le marché Polymarket le plus pertinent pour un article.
        Retourne (market, score) — score = nb mots-clés communs.
        """
        title_words = set(
            w.lower()
            for w in re.findall(r'\b\w{3,}\b', article.get("title", ""))
            if w.lower() not in STOP_WORDS
        )
        if len(title_words) < 2:
            return None, 0

        best_market = None
        best_score = 0

        for market in markets:
            combined = (
                market.get("question", "") + " " +
                market.get("description", "")
            )
            market_words = set(
                w.lower()
                for w in re.findall(r'\b\w{3,}\b', combined)
                if w.lower() not in STOP_WORDS
            )
            score = len(title_words & market_words)
            if score > best_score:
                best_score = score
                best_market = market

        return best_market, best_score

    def stop(self):
        self._running = False
        logger.info("Agent 14 (News Flash) arrêté")
