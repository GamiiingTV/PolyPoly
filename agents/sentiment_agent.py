"""
PolyPoly — Agent 2 : Sentiment & Arbitrage Narratif
Twitter, Reddit, RSS — analyse le sentiment et compare aux prix du marché.
"""

import asyncio
import json
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
try:
    from agents.llm_validator import LLMValidator
except Exception:
    LLMValidator = None  # type: ignore
try:
    from agents.metaculus_agent import MetaculusAgent
except Exception:
    MetaculusAgent = None  # type: ignore


class _VelocityTracker:
    """Suit la vélocité des news — détecte les pics d'articles par topic."""
    def __init__(self, window_size: int = 5):
        from collections import deque
        self._counts: dict[str, deque] = {}  # topic → historique des counts
        self._window = window_size

    def record(self, topic: str, count: int):
        from collections import deque
        if topic not in self._counts:
            self._counts[topic] = deque(maxlen=self._window)
        self._counts[topic].append(count)

    def velocity_multiplier(self, topic: str, count: int) -> float:
        """Retourne un multiplicateur de confiance (1.0 = normal, >1.0 = pic)."""
        history = self._counts.get(topic)
        if not history or len(history) < 2:
            return 1.0
        avg = sum(history) / len(history)
        if avg < 3:
            return 1.0
        ratio = count / avg
        if ratio >= 3.0:
            return 1.12   # Pic massif (+12% confiance)
        if ratio >= 2.0:
            return 1.07   # Pic modéré (+7% confiance)
        return 1.0


class SentimentAgent:
    """
    Agent 2 — Analyse de sentiment multi-sources.

    Responsabilités :
    - Scrape Twitter/X, Reddit, flux RSS
    - Analyse de sentiment (VADER + heuristiques)
    - Compare le narratif populaire aux prix Polymarket
    - Détecte les décalages (arbitrage de sentiment)
    - Validation LLM + consensus Metaculus avant alerte
    - Génère des signaux sur les marchés concernés
    """

    def __init__(self, db: Database, telegram: TelegramNotifier,
                 llm_validator=None, metaculus=None):
        self.db = db
        self.telegram = telegram
        self._llm = llm_validator
        self._metaculus = metaculus
        self._running = False
        self._vader = SentimentIntensityAnalyzer() if VADER_AVAILABLE else None
        self._twitter_client = None
        self._reddit_client = None
        self._http = httpx.AsyncClient(timeout=20.0)
        self._velocity = _VelocityTracker(window_size=6)

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

        # Récupérer les marchés actifs — triple filtre :
        # 1. Prix entre 5¢ et 85¢ (exclut quasi-résolus)
        # 2. end_date dans le futur (exclut matchs/événements terminés)
        # 3. Marché encore actif selon le flag active
        from datetime import timezone as _tz
        _now = datetime.now(_tz.utc)

        def _market_still_live(m: dict) -> bool:
            # Filtre prix
            price = m.get("yes_price", 0.5)
            if price < 0.05 or price > 0.85:
                return False
            # Filtre flag active
            if m.get("active") is False:
                return False
            # Filtre end_date officielle Polymarket
            end_str = m.get("end_date")
            if end_str:
                try:
                    ed = str(end_str).replace("Z", "+00:00")
                    end_dt = datetime.fromisoformat(ed)
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=_tz.utc)
                    if end_dt <= _now:
                        return False
                except Exception:
                    pass
            # Filtre date dans le SLUG/URL — critique pour le sport
            # Ex: "atp-draxl-galarne-2026-03-29" → date 29/03 passée → filtré
            # Polymarket résout 24-48h après l'événement, mais l'event est déjà fini
            url = m.get("market_url", "") or m.get("id", "")
            slug_date = re.search(r'(\d{4}-\d{2}-\d{2})', url)
            if slug_date:
                try:
                    event_date = datetime.fromisoformat(slug_date.group(1)).replace(tzinfo=_tz.utc)
                    if event_date.date() < _now.date():
                        return False  # L'événement a eu lieu avant aujourd'hui
                except Exception:
                    pass
            return True

        all_markets = await self.db.get_active_markets(limit=100)
        markets = [m for m in all_markets if _market_still_live(m)]
        logger.info(f"Sentiment: {len(markets)}/{len(all_markets)} marchés encore actifs")
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
        raw_signals = []
        for market in markets:
            signal = await self._analyze_market_sentiment(market, all_texts)
            if signal:
                raw_signals.append(signal)

        # Dédupliquer : garder uniquement le signal au plus fort edge
        # par "topic" (premiers 4 mots de la question) pour éviter les
        # alertes répétitives sur des marchés corrélés (ex: BTC $60k / $65k)
        signals = self._deduplicate_signals(raw_signals)

        logger.info(f"Sentiment: {len(signals)} signaux générés ({len(raw_signals)} avant dédup)")
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

        if len(relevant_texts) < 7:
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

        # Bonus de vélocité : si le volume d'articles sur ce topic a soudainement spikété
        topic_key = " ".join(market.get("question", "").lower().split()[:3])
        n_relevant = len(relevant_texts)
        self._velocity.record(topic_key, n_relevant)
        vel_mult = self._velocity.velocity_multiplier(topic_key, n_relevant)
        if vel_mult > 1.0:
            confidence = min(confidence * vel_mult, 0.90)
            logger.info(f"Vélocité news x{vel_mult:.2f} sur: {topic_key}")

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
            "market_url": self._get_market_url(market),
            "urgency_bonus": market.get("urgency_bonus", 0),
            "category": market.get("category", "other"),
        }

        # ── Calibration par catégorie (win rate historique) ─────────────
        cat_wr = await self.db.get_param("category_win_rates", {})
        cat = market.get("category", "other")
        if isinstance(cat_wr, dict) and cat in cat_wr:
            historical_wr = cat_wr[cat]
            if historical_wr > 0.60:
                signal["confidence"] = min(signal["confidence"] * 1.08, 0.92)
                logger.debug(f"Catégorie '{cat}' ({historical_wr:.0%} WR) → boost confiance")
            elif historical_wr < 0.45:
                signal["confidence"] = max(signal["confidence"] * 0.88, 0.0)
                logger.debug(f"Catégorie '{cat}' ({historical_wr:.0%} WR) → pénalité confiance")

        # ── Validation LLM (Claude) ──────────────────────────────────────
        if self._llm:
            signal = await self._llm.validate(signal, relevant_texts)
            if not signal.get("llm_valid", True):
                logger.info(f"Signal rejeté par LLM: {market['question'][:50]}")
                return None  # LLM a détecté un faux positif

        # ── Cross-validation Metaculus ───────────────────────────────────
        if self._metaculus:
            consensus = await self._metaculus.get_expert_consensus(market)
            if consensus:
                expert_prob = consensus["expert_prob"]
                meta_edge = expert_prob - yes_price
                # Ajuster la confiance selon l'accord Metaculus
                if abs(meta_edge - edge) < 0.15:  # Metaculus confirme
                    signal["confidence"] = min(signal["confidence"] + 0.05, 0.92)
                    signal["metaculus_prob"] = expert_prob
                    signal["metaculus_source"] = consensus["source"]
                    signal["metaculus_url"] = consensus.get("url", "")
                elif meta_edge * edge < 0:  # Metaculus contredit
                    signal["confidence"] = max(signal["confidence"] - 0.10, 0.0)
                    logger.info(
                        f"Metaculus contredit signal: poly={yes_price:.0%} "
                        f"meta={expert_prob:.0%} | {market['question'][:50]}"
                    )

        # Sauvegarder le signal
        await self.db.save_signal(signal)
        logger.info(
            f"Signal sentiment: {direction} {market['question'][:50]} "
            f"| edge={edge:.2%} | conf={signal['confidence']:.2%}"
        )

        # Notifier Telegram si signal fort
        if signal["confidence"] >= 0.70:
            await self.telegram.notify_opportunity(signal)

        return signal

    @staticmethod
    def _deduplicate_signals(signals: list[dict]) -> list[dict]:
        """
        Garde un seul signal par topic (pour éviter BTC $60k + BTC $65k + BTC $68k).
        Topic = 3 premiers mots NON-numériques et significatifs de la question.
        Garde le signal avec le plus grand |edge|.
        """
        stop = {"will", "the", "a", "an", "in", "on", "at", "to", "for",
                "of", "and", "or", "is", "be", "by", "as", "it", "hit",
                "dip", "price", "above", "below", "reach", "end", "high",
                "low", "march", "april", "may", "june", "2026", "2025"}

        def topic_key(signal: dict) -> str:
            # Supprimer les chiffres et symboles monétaires pour grouper
            # "BTC $60k", "BTC $65k", "Crude Oil $100", "Crude Oil $120" ensemble
            question = re.sub(r'[\$\£\€]?\d[\d,\.]*[kmbt]?', '', signal.get("question", "").lower())
            words = re.findall(r'\b[a-z]{3,}\b', question)
            keywords = [w for w in words if w not in stop][:3]
            return " ".join(keywords)

        best: dict[str, dict] = {}
        for sig in signals:
            key = topic_key(sig)
            if key not in best or abs(sig["edge"]) > abs(best[key]["edge"]):
                best[key] = sig
        return list(best.values())

    @staticmethod
    def _get_market_url(market: dict) -> str:
        """Extrait l'URL Polymarket depuis market_url ou raw_data."""
        url = market.get("market_url", "")
        if url:
            return url
        # Fallback: chercher dans raw_data JSON
        raw = market.get("raw_data", "")
        if raw:
            try:
                data = json.loads(raw) if isinstance(raw, str) else raw
                url = data.get("market_url", "")
                if url:
                    return url
                # Construire depuis slug si disponible
                group_slug = data.get("groupSlug") or data.get("group_slug", "")
                slug = data.get("slug", "")
                if group_slug:
                    return f"https://polymarket.com/event/{group_slug}"
                if slug:
                    return f"https://polymarket.com/market/{slug}"
            except Exception:
                pass
        return ""

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
