"""
Lancement :
    python -m memecrawler            # mode défini par MC_MODE dans .env
    python -m memecrawler --paper    # force la simulation
    python -m memecrawler --dry      # crawl + Jev seulement, aucun ordre
    python -m memecrawler --once     # un seul cycle puis quitte
"""

import argparse
import sys

from loguru import logger

from . import settings
from .bot import Bot


def main():
    ap = argparse.ArgumentParser(prog="memecrawler")
    ap.add_argument("--paper", action="store_true", help="simulation, même si MC_MODE=live")
    ap.add_argument("--dry", action="store_true", help="aucun ordre, juste crawl + juge")
    ap.add_argument("--once", action="store_true", help="un seul cycle")
    args = ap.parse_args()

    settings.LOGS_DIR.mkdir(exist_ok=True)
    logger.add(settings.LOGS_DIR / "memecrawler.log", rotation="10 MB", retention=5)

    live = settings.MODE == "live" and not args.paper
    if live and not settings.SOLANA_PRIVATE_KEY:
        sys.exit("MC_MODE=live mais SOLANA_PRIVATE_KEY est vide dans .env")
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY vide : Jev ne pourra pas juger, aucun pick possible")

    try:
        Bot(live=live, dry=args.dry).run(once=args.once)
    except KeyboardInterrupt:
        logger.info("Arrêt demandé")


if __name__ == "__main__":
    main()
