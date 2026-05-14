#!/usr/bin/env python3
"""
run_hft.py — Point d'entrée du bot HFT BTC Polymarket.

Usage :
    python run_hft.py              # mode simulation (sans clés API)
    python run_hft.py --live       # mode live (nécessite .env configuré)
    python run_hft.py --check      # vérifie la config et quitte

Variables .env requises pour le mode live :
    POLYMARKET_API_KEY, POLYMARKET_API_SECRET, POLYMARKET_API_PASSPHRASE
    POLYMARKET_PRIVATE_KEY (wallet Polygon)

Variables optionnelles :
    HFT_CAPITAL_USD         (défaut : 1000.0)
    HFT_RISK_PER_TRADE      (défaut : 0.005 = 0.5%)
    CRYPTOQUANT_API_KEY     (optionnel — fallback Binance si absent)
"""

import asyncio
import os
import sys
import signal as os_signal
from pathlib import Path


def _check_python_version() -> None:
    if sys.version_info < (3, 11):
        print("Python ≥ 3.11 requis", file=sys.stderr)
        sys.exit(1)


def _check_dependencies() -> None:
    missing = []
    required = [
        ("websockets", "websockets"),
        ("aiohttp", "aiohttp"),
        ("httpx", "httpx"),
        ("numpy", "numpy"),
        ("loguru", "loguru"),
        ("dotenv", "python-dotenv"),
    ]
    for module, pip_name in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(pip_name)
    if missing:
        print(f"Dépendances manquantes : {', '.join(missing)}", file=sys.stderr)
        print(f"→ pip install {' '.join(missing)}", file=sys.stderr)
        sys.exit(1)


def _check_config() -> None:
    """Vérifie la configuration et affiche un résumé."""
    from dotenv import load_dotenv
    load_dotenv()

    print("\n── Configuration HFT Bot ──────────────────────────────")

    capital = float(os.getenv("HFT_CAPITAL_USD", "1000.0"))
    risk_pct = float(os.getenv("HFT_RISK_PER_TRADE", "0.005"))
    daily_limit_pct = float(os.getenv("HFT_DAILY_RISK_LIMIT", "0.02"))
    hard_stop_pct = float(os.getenv("HFT_HARD_STOP", "0.004"))

    print(f"  Capital           : ${capital:.2f}")
    print(f"  Risque/trade      : {risk_pct*100:.1f}% (${capital*risk_pct:.2f})")
    print(f"  Limite quotidienne: {daily_limit_pct*100:.1f}% (${capital*daily_limit_pct:.2f})")
    print(f"  Arrêt dur         : {hard_stop_pct*100:.2f}% (${capital*hard_stop_pct:.2f})")

    print("\n── APIs ──────────────────────────────────────────────")

    poly_key = os.getenv("POLYMARKET_API_KEY", "")
    poly_secret = os.getenv("POLYMARKET_API_SECRET", "")
    poly_wallet = os.getenv("POLYMARKET_PRIVATE_KEY", "")
    cq_key = os.getenv("CRYPTOQUANT_API_KEY", "")

    live_ready = bool(poly_key and poly_secret and poly_wallet)
    print(f"  Polymarket API    : {'✓ configuré' if live_ready else '✗ manquant — mode simulation'}")
    print(f"  CryptoQuant API   : {'✓ configuré' if cq_key else '○ absent — fallback Binance public'}")

    try:
        from tradingview_ta import TA_Handler
        print("  TradingView TA    : ✓ installé")
    except ImportError:
        print("  TradingView TA    : ✗ non installé (pip install tradingview-ta)")

    print("\n── Mode ──────────────────────────────────────────────")
    if live_ready:
        print("  → MODE LIVE (ordres réels sur Polymarket)")
    else:
        print("  → MODE SIMULATION (aucun ordre réel)")

    print("──────────────────────────────────────────────────────\n")

    return live_ready


def _try_uvloop() -> None:
    """Active uvloop si disponible (boucle async 2-4x plus rapide)."""
    try:
        import uvloop
        uvloop.install()
        print("uvloop activé (performance maximale)")
    except ImportError:
        print("uvloop non disponible — asyncio standard utilisé")
        print("  → pip install uvloop  (recommandé pour HFT)")


async def _main() -> None:
    from hft.bot import HFTBot

    bot = HFTBot()

    # Gestion SIGINT / SIGTERM pour arrêt propre
    loop = asyncio.get_running_loop()

    def _handle_signal() -> None:
        print("\nSignal reçu — arrêt propre du bot...")
        asyncio.ensure_future(bot.stop())
        loop.stop()

    for sig in (os_signal.SIGINT, os_signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_signal)

    await bot.run()


def main() -> None:
    _check_python_version()
    _check_dependencies()

    args = sys.argv[1:]

    if "--check" in args:
        _check_config()
        sys.exit(0)

    # Ensure logs dir exists
    Path("logs").mkdir(exist_ok=True)

    # Afficher la config au démarrage
    live_ready = _check_config()

    if "--live" in args and not live_ready:
        print("ERREUR : --live demandé mais clés Polymarket manquantes dans .env")
        sys.exit(1)

    _try_uvloop()

    print("Démarrage du bot HFT...")
    print("Ctrl+C pour arrêter proprement\n")

    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        print("\nArrêté par l'utilisateur")


if __name__ == "__main__":
    main()
