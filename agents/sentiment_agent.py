"""
PolyPoly — Agent 2 : Sentiment & Arbitrage Narratif
Twitter, Reddit, RSS — analyse le sentiment et compare aux prix du marché.
"""

import asyncio
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Optional
import httpx
from loguru import logger

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    FEEDPARSER_AVAILABLE = False

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

from config import (
    TWITTER_BEARER_TOKEN, TWITTER_KEYWORDS,
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, REDDIT_SUBREDDITS,
    RSS_FEEDS, SENTIMENT_INTERVAL_SEC, MIN_EDGE_THRESHOLD,
)
from utils.database import Database
try:
    from utils.telegram_bot import TelegramNotifier
except Exception:
    TelegramNotifier = object  # type: ignore


class SentimentAgent:
    """
    Agent 2 — Analyse de sentiment multi-sources.

    Responsabilités :
    - Scrape Twitter/X, Reddit, flux RSS
    - Analyse de sentiment (VADER + heuristiques)
    - Compare le narratif populaire aux prix Polymarket
    - Détecte les décalages (arbitrage de sentiment)
    - Génère des signaux sur les marchés concernés
    """

    def __init__(self, db: Database, telegram: TelegramNotifier):
        self.db = db
        self.telegram = telegram
        self._running = False
        self._vader = SentimentIntensityAnalyzer() if VADER_AVAILABLE else None
        self._twitter_client = None
        self._reddit_client = None
        self._http = httpx.AsyncClient(timeout=20.0)

    async def start(self) -> None:
        """Initialise les clients API."""
        # Twitter
        if TWEEPY_AVAILABLE and TWITTER_BEARER_TOKEN:
            try:
                self._twitter_client = tweepy.Client(
                    bearer_token=TWITTER_BEARER_TOKEN,
                    wait_on_rate_limit=True,
                )
                logger.info("Twitter API connectée")
            except Exception as e:
                logger.warning(f"Twitter non disponible: {e}")

        # Reddit
        if PRAW_AVAILABLE and REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
            try:
                self._reddit_client = praw.Reddit(
                    client_id=REDDIT_CLIENT_ID,
                    client_secret=REDDIT_CLIENT_SECRET,
                    user_agent=REDDIT_USER_AGENT,
                )
                logger.info("Reddit API connectée")
            except Exception as e:
                logger.warning(f"Reddit non disponible: {e}")

    async def run_forever(self) -> None:
        """Boucle principale."""
        await self.start()
        self._running = True
        logger.info("Agent 2 (Sentiment) démarré")
        while self._running:
            try:
                await self.analysis_cycle()
            except Exception as e:
                logger.error(f"Sentiment erreur: {e}")
                await self.telegram.notify_error(str(e), "Agent 2 - Sentiment")
            await asyncio.sleep(SENTIMENT_INTERVAL_SEC)

    async def analysis_cycle(self) -> list[dict]:
        """Cycle complet d'analyse de sentiment."""
        logger.info("Sentiment: démarrage analyse...")

        # Récupérer les marchés actifs
        markets = await self.db.get_active_markets(limit=50)
        if not markets:
            return []

        # Collecter les données de toutes les sources en parallèle
        twitter_data, reddit_data, rss_data = await asyncio.gather(
            self._fetch_twitter_data(),
            self._fetch_reddit_data(),
            self._fetch_rss_data(),
            return_exceptions=True,
        )

        # Combiner toutes les données textuelles
        all_texts = []
        if isinstance(twitter_data, list):
            all_texts.extend(twitter_data)
        if isinstance(reddit_data, list):
            all_texts.extend(reddit_data)
        if isinstance(rss_data, list):
            all_texts.extend(rss_data)

        logger.info(f"Sentiment: {len(all_texts)} textes collectés")

        # Analyser chaque marché
        signals = []
        for market in markets:
            signal = await self._analyze_market_sentiment(market, all_texts)
            if signal:
                signals.append(signal)

        logger.info(f"Sentiment: {len(signals)} signaux générés")
        return signals

    async def _fetch_twitter_data(self) -> list[str]:
        """Récupère les tweets récents via tweepy.Client (sync) dans un executor."""
        if not self._twitter_client:
            return []

        def _sync_fetch():
            texts = []
            try:
                query = " OR ".join(f'"{kw}"' for kw in TWITTER_KEYWORDS[:5])
                query += " -is:retweet lang:en"
                response = self._twitter_client.search_recent_tweets(
                    query=query,
                    max_results=100,
                    tweet_fields=["text", "created_at", "public_metrics"],
                )
                if response.data:
                    for tweet in response.data:
                        metrics = getattr(tweet, "public_metrics", {}) or {}
                        likes = metrics.get("like_count", 0)
                        rts = metrics.get("retweet_count", 0)
                        weight = 1 + min((likes + rts * 2) / 50, 5)
                        texts.extend([tweet.text] * int(weight))
            except Exception as e:
                logger.warning(f"Twitter fetch erreur: {e}")
            return texts

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_fetch)

    async def _fetch_reddit_data(self) -> list[str]:
        """Récupère les posts Reddit récents."""
        texts = []
        if not self._reddit_client:
            return texts

        try:
            # Utiliser un executor pour le code synchrone PRAW
            loop = asyncio.get_event_loop()

            def fetch_reddit():
                posts = []
                for sub_name in REDDIT_SUBREDDITS[:4]:
                    try:
                        sub = self._reddit_client.subreddit(sub_name)
                        for post in sub.hot(limit=25):
                            combined = f"{post.title} {post.selftext[:300]}"
                            score_weight = 1 + min(post.score / 100, 5)
                            posts.extend([combined] * int(score_weight))
                            # Commentaires top
                            post.comments.replace_more(limit=0)
                            for comment in list(post.comments)[:5]:
                                posts.append(comment.body[:200])
                    except Exception:
                        continue
                return posts

            texts = await loop.run_in_executor(None, fetch_reddit)

        except Exception as e:
            logger.warning(f"Reddit fetch erreur: {e}")

        return texts

    async def _fetch_rss_data(self) -> list[str]:
        """
        Récupère les actualités via RSS avec pondération temporelle.
        Les articles récents sont répétés plus souvent (poids exponentiel).
        """
        tasks = [self._fetch_single_rss(url) for url in RSS_FEEDS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        weighted_texts: list[str] = []
        for r in results:
            if not isinstance(r, list):
                continue
            for text, age_hours in r:
                if not text.strip():
                    continue
                # Pondération : article de 0h = 5x, 1h = 3x, 6h = 2x, 24h = 1x
                if age_hours < 1:
                    weight = 5
                elif age_hours < 6:
                    weight = 3
                elif age_hours < 24:
                    weight = 2
                else:
                    weight = 1
                weighted_texts.extend([text] * weight)

        return weighted_texts

    @staticmethod
    def _parse_rss_date(date_str: str) -> float:
        """Parse une date RSS et retourne l'âge en heures (0 = maintenant)."""
        if not date_str:
            return 24.0
        import email.utils
        try:
            parsed = email.utils.parsedate_to_datetime(date_str)
            age = (datetime.now(timezone.utc) - parsed).total_seconds() / 3600
            return max(0.0, age)
        except Exception:
            pass
        # Essai format ISO
        try:
            parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - parsed).total_seconds() / 3600
            return max(0.0, age)
        except Exception:
            return 24.0

    async def _fetch_single_rss(self, url: str) -> list[tuple[str, float]]:
        """
        Fetch un seul flux RSS.
        Retourne une liste de (texte, age_heures) pour pondération temporelle.
        """
        items: list[tuple[str, float]] = []
        try:
            resp = await self._http.get(url)
            if FEEDPARSER_AVAILABLE:
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:20]:
                    title = getattr(entry, "title", "")
                    summary = getattr(entry, "summary", "")
                    pub = getattr(entry, "published", "") or getattr(entry, "updated", "")
                    age = self._parse_rss_date(pub)
                    items.append((f"{title} {summary[:200]}", age))
            else:
                root = ET.fromstring(resp.text)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                for item in root.findall(".//item")[:20]:
                    title = item.findtext("title") or ""
                    desc = item.findtext("description") or ""
                    pub = item.findtext("pubDate") or ""
                    age = self._parse_rss_date(pub)
                    items.append((f"{title} {desc[:200]}", age))
                for entry in root.findall(".//atom:entry", ns)[:20]:
                    title = entry.findtext("atom:title", namespaces=ns) or ""
                    summary = entry.findtext("atom:summary", namespaces=ns) or ""
                    pub = entry.findtext("atom:updated", namespaces=ns) or ""
                    age = self._parse_rss_date(pub)
                    items.append((f"{title} {summary[:200]}", age))
        except Exception:
            pass
        return items

    def _compute_sentiment(self, texts: list[str]) -> float:
        """
        Calcule un score de sentiment global.
        Retourne une valeur entre -1 (très négatif) et +1 (très positif).
        """
        if not texts or not self._vader:
            return 0.0

        scores = []
        for text in texts[:200]:  # Limiter pour la perf
            if text and len(text) > 10:
                vs = self._vader.polarity_scores(text)
                scores.append(vs["compound"])

        if not scores:
            return 0.0

        # Moyenne pondérée (plus de poids aux scores extrêmes)
        return float(sum(scores) / len(scores))

    def _find_relevant_texts(self, market: dict, all_texts: list[str]) -> list[str]:
        """Trouve les textes pertinents pour un marché donné."""
        question = market.get("question", "").lower()

        # Extraire mots-clés de la question
        stop_words = {"will", "the", "a", "an", "in", "on", "at", "to", "for",
                      "of", "and", "or", "is", "be", "by", "as", "it", "this"}
        keywords = [
            w for w in re.findall(r'\b\w{3,}\b', question)
            if w not in stop_words
        ][:6]

        if not keywords:
            return []

        relevant = []
        for text in all_texts:
            text_lower = text.lower()
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches >= 2:  # Au moins 2 mots-clés en commun
                relevant.append(text)

        return relevant

    async def _analyze_market_sentiment(
        self, market: dict, all_texts: list[str]
    ) -> Optional[dict]:
        """
        Analyse le sentiment pour un marché spécifique.
        Retourne un signal si un décalage est détecté.
        """
        relevant_texts = self._find_relevant_texts(market, all_texts)

        if len(relevant_texts) < 3:
            return None

        sentiment_score = self._compute_sentiment(relevant_texts)
        yes_price = market.get("yes_price", 0.5)

        # Convertir le sentiment en probabilité implicite
        # sentiment entre -1 et 1 → probabilité entre 0.2 et 0.8
        implied_prob = 0.5 + sentiment_score * 0.3

        # Calculer l'écart (edge)
        edge = implied_prob - yes_price

        # Seuil de signal : edge significatif ET sentiment suffisamment fort
        abs_edge = abs(edge)
        if abs_edge < MIN_EDGE_THRESHOLD or abs(sentiment_score) < 0.15:
            return None

        direction = "YES" if edge > 0 else "NO"
        confidence = min(0.5 + abs(sentiment_score) * 0.3 + abs_edge * 0.5, 0.85)

        signal = {
            "market_id": market["id"],
            "question": market.get("question", ""),
            "signal_type": "SENTIMENT",
            "direction": direction,
            "confidence": round(confidence, 4),
            "edge": round(edge, 4),
            "predicted_prob": round(implied_prob, 4),
            "market_price": round(yes_price, 4),
            "sentiment_score": round(sentiment_score, 4),
            "source": f"Sentiment ({len(relevant_texts)} textes)",
            "texts_count": len(relevant_texts),
            "market_url": market.get("market_url", ""),
        }

        # Sauvegarder le signal
        await self.db.save_signal(signal)
        logger.info(
            f"Signal sentiment: {direction} {market['question'][:50]} "
            f"| edge={edge:.2%} | conf={confidence:.2%}"
        )

        # Notifier Telegram si signal fort
        if confidence >= 0.70:
            await self.telegram.notify_opportunity(signal)

        return signal

    async def get_sentiment_for_market(self, market_id: str) -> Optional[float]:
        """Retourne le dernier score de sentiment pour un marché."""
        signals = await self.db.get_recent_signals(limit=100)
        for sig in signals:
            if sig["market_id"] == market_id and sig["signal_type"] == "SENTIMENT":
                return sig.get("sentiment_score", 0.0)
        return None

    def stop(self):
        self._running = False
        logger.info("Agent 2 (Sentiment) arrêté")
