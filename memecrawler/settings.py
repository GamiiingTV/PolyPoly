"""
MemeCrawler — Configuration (lue depuis le .env à la racine de PolyPoly)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _f(name: str, default: float) -> float:
    return float(os.getenv(name, default))


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
STATE_FILE = DATA_DIR / "memecrawler_state.json"
STOP_FILE = BASE_DIR / "STOP_MEMECRAWLER"   # crée ce fichier = plus aucun achat

# --- Mode : "live" (vrai argent via Jupiter) ou "paper" (simulation) ---
MODE: str = os.getenv("MC_MODE", "paper").lower()

# --- Solana / Jupiter ---
SOLANA_PRIVATE_KEY: str = os.getenv("SOLANA_PRIVATE_KEY", "")
SOLANA_RPC_URL: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
JUPITER_API_URL: str = os.getenv("JUPITER_API_URL", "https://lite-api.jup.ag/swap/v1")
JUPITER_API_KEY: str = os.getenv("JUPITER_API_KEY", "")
SLIPPAGE_BPS: int = int(os.getenv("MC_SLIPPAGE_BPS", 300))
PRIORITY_FEE_LAMPORTS: int = int(os.getenv("MC_PRIORITY_FEE_LAMPORTS", 100_000))
SOL_RESERVE: float = _f("MC_SOL_RESERVE", 0.02)   # SOL gardés pour les frais

# --- Jev (juge IA) ---
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
JEV_MODEL: str = os.getenv("MC_JEV_MODEL", "claude-haiku-5-5")

# --- Taille / risque ---
PAPER_BANK_USD: float = _f("MC_PAPER_BANK_USD", 100.0)
PAPER_COST_PCT: float = _f("MC_PAPER_COST_PCT", 0.015)  # slippage + frais simulés par ordre
TICKET_PCT: float = _f("MC_TICKET_PCT", 0.20)            # % de la bank par trade
MAX_TICKET_USD: float = _f("MC_MAX_TICKET_USD", 50.0)    # plafond absolu par trade
MAX_TICKET_LIQ_PCT: float = _f("MC_MAX_TICKET_LIQ_PCT", 0.02)  # ticket ≤ 2 % de la liquidité
DAILY_LOSS_LIMIT_USD: float = _f("MC_DAILY_LOSS_LIMIT_USD", 30.0)

# --- Stratégie : « no entry without a flush first » ---
FLUSH_PCT: float = _f("MC_FLUSH_PCT", 0.25)        # baisse depuis le sommet pour valider un flush
REBOUND_PCT: float = _f("MC_REBOUND_PCT", 0.03)    # remontée depuis le creux avant d'entrer
MAX_H1_DROP: float = _f("MC_MAX_H1_DROP", -50.0)   # « nobody buys a coin halving on the hour »
STOP_LOSS: float = _f("MC_STOP_LOSS", 0.12)
TRAIL_START: float = _f("MC_TRAIL_START", 0.15)    # trailing stop activé à +15 %
TRAIL_PCT: float = _f("MC_TRAIL_PCT", 0.10)        # vend si -10 % depuis le plus haut
MAX_HOLD_MIN: float = _f("MC_MAX_HOLD_MIN", 240)
RUG_LIQ_DROP: float = _f("MC_RUG_LIQ_DROP", 0.50)  # liquidité -50 % depuis l'entrée = sortie
WATCH_HOURS: float = _f("MC_WATCH_HOURS", 12)      # durée de suivi d'un pick

# --- Boucle ---
CRAWL_INTERVAL_S: float = _f("MC_CRAWL_INTERVAL_S", 60)
TICK_INTERVAL_S: float = _f("MC_TICK_INTERVAL_S", 15)
RETRY_AFTER_MIN: float = _f("MC_RETRY_AFTER_MIN", 10)   # re-check d'un coin trop jeune
RETRY_WINDOW_H: float = _f("MC_RETRY_WINDOW_H", 3)

# --- Telegram (optionnel, réutilise les variables de PolyPoly) ---
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
