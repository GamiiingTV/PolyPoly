"""
PolyPoly — Configuration Centrale
Tous les paramètres du bot sont ici.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CHEMINS
# ============================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
MODELS_DIR = BASE_DIR / "models"

for d in [DATA_DIR, LOGS_DIR, MODELS_DIR]:
    d.mkdir(exist_ok=True)

# ============================================================
# POLYMARKET
# ============================================================
POLYMARKET_PRIVATE_KEY: str = os.getenv("POLYMARKET_PRIVATE_KEY", "")
POLYMARKET_API_KEY: str = os.getenv("POLYMARKET_API_KEY", "")
POLYMARKET_API_SECRET: str = os.getenv("POLYMARKET_API_SECRET", "")
POLYMARKET_API_PASSPHRASE: str = os.getenv("POLYMARKET_API_PASSPHRASE", "")
POLYMARKET_PROXY_ADDRESS: str = os.getenv("POLYMARKET_PROXY_ADDRESS", "")

CLOB_API_URL = "https://clob.polymarket.com"
GAMMA_API_URL = "https://gamma-api.polymarket.com"
POLYGON_RPC_URL: str = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")

# ============================================================
# LLM
# ============================================================
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# ============================================================
# THE ODDS API (cotes bookmaker professionnelles — gratuit)
# Inscription : https://the-odds-api.com  (500 req/mois gratuit)
# ============================================================
ODDS_API_KEY: str = os.getenv("ODDS_API_KEY", "")
LLM_MODEL = "claude-sonnet-4-6"          # Modèle Claude par défaut
LLM_MAX_TOKENS = 2048
LLM_TEMPERATURE = 0.1                     # Bas pour décisions financières

# ============================================================
# RÉSEAUX SOCIAUX
# ============================================================
TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")
TWITTER_API_KEY: str = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET: str = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN: str = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET: str = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "PolyPolyBot/1.0")

RSS_FEEDS = [
    # Actualités générales
    "https://feeds.reuters.com/reuters/topNews",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.cnn.com/rss/edition.rss",
    "https://feeds.npr.org/1001/rss.xml",
    "https://www.politico.com/rss/politicopicks.xml",
    "https://thehill.com/homenews/feed/",
    "https://feeds.bloomberg.com/politics/news.rss",
    "https://www.axios.com/feeds/feed.rss",
    "https://feeds.washingtonpost.com/rss/world",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    # Crypto / Finance
    "https://cointelegraph.com/rss",
    "https://coindesk.com/arc/outboundfeeds/rss/",
    "https://decrypt.co/feed",
    "https://cryptonews.com/news/feed/",
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "https://finance.yahoo.com/rss/topfinstories",
    # Sport
    "https://feeds.bbci.co.uk/sport/rss.xml",
    "https://www.espn.com/espn/rss/news",
    "https://www.skysports.com/rss/12040",
    # Politique US / Géopolitique
    "https://www.foreignaffairs.com/rss.xml",
    "https://theintercept.com/feed/?rss",
]

TWITTER_KEYWORDS = [
    "polymarket", "prediction market", "election", "crypto", "bitcoin",
    "fed rate", "inflation", "geopolitics", "breaking news", "market odds"
]

REDDIT_SUBREDDITS = [
    "polymarket", "PredictionMarkets", "worldnews", "politics",
    "economics", "investing", "wallstreetbets", "news"
]

# ============================================================
# TELEGRAM
# ============================================================
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# ============================================================
# PARAMÈTRES DE TRADING
# ============================================================
MAX_TRADE_SIZE_USD: float = float(os.getenv("MAX_TRADE_SIZE_USD", "5.0"))
CAPITAL_USD: float = float(os.getenv("CAPITAL_USD", "100.0"))
MAX_OPEN_POSITIONS: int = int(os.getenv("MAX_OPEN_POSITIONS", "10"))
DAILY_LOSS_LIMIT_USD: float = float(os.getenv("DAILY_LOSS_LIMIT_USD", "15.0"))

# Seuils de qualité
MIN_CONFIDENCE_THRESHOLD: float = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "0.65"))
MIN_EDGE_THRESHOLD: float = float(os.getenv("MIN_EDGE_THRESHOLD", "0.05"))   # 5% d'écart minimum
MIN_LIQUIDITY_USD: float = float(os.getenv("MIN_LIQUIDITY_USD", "1000.0"))
MIN_VOLUME_24H_USD: float = float(os.getenv("MIN_VOLUME_24H_USD", "500.0"))
MAX_TIME_TO_RESOLUTION_DAYS: int = 30    # Ne trade pas les marchés >30j
MIN_TIME_TO_RESOLUTION_HOURS: int = 1   # Ne trade pas si résolution <1h (sports inclus)

# Anomalie de prix : si le prix bouge de X% en Y minutes
PRICE_ANOMALY_THRESHOLD: float = 0.08   # 8% de mouvement
PRICE_ANOMALY_WINDOW_MIN: int = 15       # En 15 minutes
SPREAD_ANOMALY_THRESHOLD: float = 0.15  # Spread bid-ask >15%

# Nombre de marchés à scanner
TARGET_MARKETS_COUNT: int = 300

# ============================================================
# DÉTECTION DE CATÉGORIE (mots-clés → catégorie)
# ============================================================
CATEGORY_KEYWORDS: dict = {
    "crypto": [
        "bitcoin", "btc", "ethereum", "eth", "crypto", "blockchain",
        "solana", "sol", "xrp", "ripple", "defi", "nft", "binance",
        "coinbase", "stablecoin", "usdc", "usdt", "doge", "dogecoin",
    ],
    "sports": [
        "nba", "nfl", "mlb", "nhl", "soccer", "football", "basketball",
        "tennis", "golf", "mma", "ufc", "boxing", "championship",
        "world cup", "super bowl", "playoffs", "tournament", "league",
        "match", "game", "win", "score", "player", "team", "coach",
    ],
    "politics_us": [
        "trump", "biden", "harris", "democrat", "republican", "congress",
        "senate", "house", "president", "election", "vote", "white house",
        "supreme court", "fbi", "cia", "pentagon", "gop",
    ],
    "geopolitics": [
        "russia", "ukraine", "china", "taiwan", "iran", "israel",
        "nato", "war", "military", "sanctions", "nuclear", "missile",
        "ceasefire", "invasion", "conflict", "troops", "strike",
    ],
    "economics": [
        "fed", "federal reserve", "interest rate", "inflation", "gdp",
        "recession", "unemployment", "cpi", "fomc", "powell",
        "stock market", "s&p", "nasdaq", "dow", "earnings", "ipo",
        "treasury", "debt", "tariff", "trade",
    ],
    "tech": [
        "ai", "artificial intelligence", "openai", "google", "apple",
        "microsoft", "meta", "spacex", "elon musk", "tesla",
        "nvidia", "chatgpt", "gpt", "robot", "autonomous",
    ],
}

# ============================================================
# SCANNER — INTERVALLES (secondes)
# ============================================================
SCANNER_INTERVAL_SEC: int = 60          # Scan marchés toutes les 60s
SENTIMENT_INTERVAL_SEC: int = 300       # Sentiment toutes les 5min
PREDICTION_INTERVAL_SEC: int = 120      # Prédictions toutes les 2min
TRADE_CHECK_INTERVAL_SEC: int = 30      # Vérif positions toutes les 30s
LEARNING_INTERVAL_SEC: int = 3600       # Apprentissage toutes les heures

# ============================================================
# BASE DE DONNÉES
# ============================================================
DATABASE_PATH: str = os.getenv("DATABASE_PATH", str(DATA_DIR / "polypoly.db"))

# ============================================================
# LOGGING
# ============================================================
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: str = os.getenv("LOG_FILE", str(LOGS_DIR / "polypoly.log"))
LOG_ROTATION = "100 MB"
LOG_RETENTION = "30 days"

# ============================================================
# MODÈLE ML
# ============================================================
XGBOOST_MODEL_PATH = str(MODELS_DIR / "xgboost_model.pkl")
FEATURE_SCALER_PATH = str(MODELS_DIR / "feature_scaler.pkl")
XGBOOST_PARAMS = {
    "n_estimators": 500,
    "max_depth": 6,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 3,
    "gamma": 0.1,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "use_label_encoder": False,
    "eval_metric": "logloss",
    "random_state": 42,
    "n_jobs": -1,
}

# Nombre minimum de trades pour entraîner le modèle
MIN_TRADES_FOR_TRAINING: int = 50
