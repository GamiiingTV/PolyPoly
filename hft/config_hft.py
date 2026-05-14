"""
HFT BTC Polymarket Bot — Configuration
Tous les paramètres du bot HFT centralisés ici.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CAPITAL & RISQUE
# ============================================================
CAPITAL_USD: float = float(os.getenv("HFT_CAPITAL_USD", "1000.0"))

RISK_PER_TRADE_PCT: float = float(os.getenv("HFT_RISK_PER_TRADE", "0.005"))    # 0.5%
DAILY_RISK_LIMIT_PCT: float = float(os.getenv("HFT_DAILY_RISK_LIMIT", "0.02")) # 2.0%
HARD_STOP_PCT: float = float(os.getenv("HFT_HARD_STOP", "0.004"))              # 0.4%

RISK_PER_TRADE_USD: float = CAPITAL_USD * RISK_PER_TRADE_PCT
DAILY_LOSS_LIMIT_USD: float = CAPITAL_USD * DAILY_RISK_LIMIT_PCT
HARD_STOP_USD: float = CAPITAL_USD * HARD_STOP_PCT

# ── Compound automatique ──────────────────────────────────────────────────────
# Chaque gain augmente le capital actif → positions suivantes plus grandes.
# RESERVE_PCT du capital est intouchable (protection contre la ruine).
# MIN_POLY_ORDER_USD : plancher minimum d'un ordre Polymarket.
COMPOUND_ENABLED:    bool  = os.getenv("HFT_COMPOUND_ENABLED", "true").lower() == "true"
RESERVE_PCT:         float = float(os.getenv("HFT_RESERVE_PCT",   "0.20"))  # 20% réserve
MIN_POLY_ORDER_USD:  float = float(os.getenv("HFT_MIN_ORDER_USD", "1.0"))   # plancher $1

# ============================================================
# EXÉCUTION HFT
# ============================================================
MAX_EXECUTION_MS: int = 100           # Seuil d'alerte latence (ms)
HTTP_TIMEOUT_SEC: float = 0.5         # Timeout HTTP ultra-court
MAX_ORDERS_PER_SEC: int = 1000        # Capacité théorique (rate-limited par Polymarket)
POLY_RATE_LIMIT_PER_SEC: int = 10     # Limite réelle Polymarket

MIN_EDGE_PCT: float = 0.003           # 0.3% — edge minimum pour trader
TARGET_EDGE_PCT: float = 0.005        # 0.5% — cible
MAX_EDGE_PCT: float = 0.008           # 0.8% — au-delà on est trop en retard
MAX_SLIPPAGE_PCT: float = 0.005       # 0.5% slippage max toléré

MIN_LIQUIDITY_USD: float = float(os.getenv("HFT_MIN_LIQUIDITY", "5000.0"))
MAX_SPREAD_PCT: float = float(os.getenv("HFT_MAX_SPREAD", "0.02"))   # 2% bid-ask max

# ============================================================
# SIGNAUX & FORCE-GRAPH
# ============================================================
FORCE_GRAPH_CONVERGENCE_THRESHOLD: float = 0.65  # Consensus ≥ 65% pour trader
FORCE_GRAPH_ITERATIONS: int = 10
FORCE_GRAPH_ALPHA: float = 0.3        # Taux d'influence voisin par itération
MIN_SIGNAL_SCORE: float = 0.65

# Fenêtre glissante pour calibration du lag
LAG_WINDOW: int = 20
MIN_LAG_MS: float = 150.0             # Lag minimum exploitable (ms)
MAX_LAG_MS: float = 3000.0            # Au-delà, Polymarket a déjà repricé

# Mouvement de prix minimum Binance pour déclencher la détection
MIN_PRICE_MOVE_PCT: float = 0.001     # 0.1% = ~$1 sur BTC à $100k

# ============================================================
# BINANCE
# ============================================================
BINANCE_WS_BASE: str = "wss://stream.binance.com:9443/ws"
BINANCE_REST_BASE: str = "https://api.binance.com"
BINANCE_SYMBOL: str = "BTCUSDT"
BINANCE_SYMBOL_LOWER: str = "btcusdt"
CANDLE_INTERVAL: str = "5m"
CANDLE_LOOKBACK: int = 100            # Nombre de bougies 5M en mémoire

# ============================================================
# POLYMARKET
# ============================================================
POLY_WS_URL: str = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
CLOB_REST_URL: str = "https://clob.polymarket.com"
GAMMA_API_URL: str = "https://gamma-api.polymarket.com"

# Mots-clés pour trouver les marchés BTC 5M UP/DOWN
BTC_MARKET_KEYWORDS: list[str] = [
    "will btc", "will bitcoin",
    "bitcoin higher", "bitcoin lower",
    "btc higher", "btc lower",
    "btc up", "btc down",
    "5 min", "5min", "five min",
]
# Durée de résolution max pour un marché "5 minutes" (en secondes)
MAX_RESOLUTION_WINDOW_SEC: int = 600  # 10 minutes max
MARKET_REFRESH_SEC: int = 30          # Re-chercher les marchés toutes les 30s

# ============================================================
# CRYPTOQUANT
# ============================================================
CRYPTOQUANT_API_KEY: str = os.getenv("CRYPTOQUANT_API_KEY", "")
CRYPTOQUANT_BASE_URL: str = "https://api.cryptoquant.com/v1"
CRYPTOQUANT_POLL_SEC: int = 300       # Données disponibles toutes les 5min

# ============================================================
# TRADINGVIEW
# ============================================================
TV_EXCHANGE: str = "BINANCE"
TV_SYMBOL: str = "BTCUSDT"
TV_SCREENER: str = "crypto"
TV_POLL_SEC: int = 30                 # Refresh TradingView toutes les 30s
TV_TIMEOUT_SEC: int = 5

# ============================================================
# LOGGING
# ============================================================
HFT_LOG_FILE: str = str(Path("logs") / "hft.log")
HFT_LOG_LEVEL: str = os.getenv("HFT_LOG_LEVEL", "INFO")
