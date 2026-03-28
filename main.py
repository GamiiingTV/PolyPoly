"""
PolyPoly — Orchestrateur Principal
Lance et coordonne les 5 agents IA en parallèle.
"""

import asyncio
import sys
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

import config
from utils.database import Database
from utils.polymarket_api import GammaAPI, CLOBClient
from utils.telegram_bot import TelegramNotifier
from agents.market_scanner  import MarketScanner
from agents.sentiment_agent  import SentimentAgent
from agents.prediction_agent import PredictionAgent
from agents.trading_agent    import TradingAgent
from agents.learning_agent   import LearningAgent

console = Console()


def setup_logging() -> None:
    """Configure le logging avec Loguru."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level=config.LOG_LEVEL,
        colorize=True,
    )
    logger.add(
        config.LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
        level="DEBUG",
        rotation=config.LOG_ROTATION,
        retention=config.LOG_RETENTION,
        compression="zip",
    )


def print_banner() -> None:
    """Affiche la bannière de démarrage."""
    banner = Text()
    banner.append("  PolyPoly ", style="bold cyan")
    banner.append("— Polymarket AI Trading Bot\n", style="white")
    banner.append("  5 Agents IA • XGBoost + Claude • Telegram Alerts\n", style="dim white")
    banner.append(f"  Démarré: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", style="dim green")

    console.print(Panel(
        banner,
        border_style="cyan",
        padding=(1, 4),
    ))

    # Config résumée
    sim_mode = not bool(config.POLYMARKET_PRIVATE_KEY.replace("0xTON_PRIVATE_KEY_POLYGON_WALLET", ""))
    mode_str = "[yellow]SIMULATION[/yellow]" if sim_mode else "[green]LIVE[/green]"

    console.print(f"  Mode:         {mode_str}")
    console.print(f"  Max trade:    [cyan]${config.MAX_TRADE_SIZE_USD}[/cyan]")
    console.print(f"  Confiance:    [cyan]{config.MIN_CONFIDENCE_THRESHOLD:.0%}[/cyan]")
    console.print(f"  Edge min:     [cyan]{config.MIN_EDGE_THRESHOLD:.0%}[/cyan]")
    console.print(f"  Marchés cible: [cyan]{config.TARGET_MARKETS_COUNT}[/cyan]")
    console.print(f"  Telegram:     {'[green]✓[/green]' if config.TELEGRAM_BOT_TOKEN else '[red]✗ non configuré[/red]'}")
    console.print(f"  LLM:          {'[green]✓ Claude[/green]' if config.ANTHROPIC_API_KEY else '[yellow]✗ désactivé[/yellow]'}")
    console.print()


async def health_check(db: Database) -> None:
    """Affiche périodiquement un résumé de santé."""
    while True:
        await asyncio.sleep(3600)  # Toutes les heures
        try:
            stats = await db.get_trade_stats()
            markets = await db.get_active_markets(limit=1000)
            open_trades = await db.get_open_trades()

            logger.info(
                f"[HEALTH] {len(markets)} marchés | "
                f"{len(open_trades)} positions ouvertes | "
                f"Win rate: {stats.get('win_rate', 0):.1f}% | "
                f"P&L: {stats.get('total_pnl', 0):+.2f}$"
            )
        except Exception as e:
            logger.error(f"Health check erreur: {e}")


async def main() -> None:
    """Point d'entrée principal."""
    setup_logging()
    print_banner()

    # --- Initialisation des services partagés ---
    db = Database(config.DATABASE_PATH)
    await db.connect()
    logger.info("Database initialisée")

    gamma = GammaAPI()
    clob = CLOBClient()
    telegram = TelegramNotifier()
    await telegram.start()

    # --- Instanciation des 5 agents ---
    scanner   = MarketScanner(db, gamma, telegram)
    sentiment = SentimentAgent(db, telegram)
    predictor = PredictionAgent(db, telegram)
    trader    = TradingAgent(db, clob, gamma, telegram)
    learner   = LearningAgent(db, telegram)

    logger.info("5 agents initialisés")

    # Premier scan immédiat pour peupler la DB
    logger.info("Scan initial des marchés...")
    await scanner.scan_cycle()

    # --- Lancement concurrent de tous les agents ---
    tasks = [
        asyncio.create_task(scanner.run_forever(),   name="Agent1-Scanner"),
        asyncio.create_task(sentiment.run_forever(),  name="Agent2-Sentiment"),
        asyncio.create_task(predictor.run_forever(),  name="Agent3-Prediction"),
        asyncio.create_task(trader.run_forever(),     name="Agent4-Trading"),
        asyncio.create_task(learner.run_forever(),    name="Agent5-Learning"),
        asyncio.create_task(health_check(db),         name="HealthCheck"),
    ]

    console.print("[bold green]Tous les agents sont opérationnels ![/bold green]\n")
    logger.info("PolyPoly opérationnel — Ctrl+C pour arrêter")

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        logger.info("Arrêt demandé par l'utilisateur")
    finally:
        # Arrêt propre
        logger.info("Arrêt des agents...")
        for task in tasks:
            task.cancel()

        scanner.stop()
        sentiment.stop()
        predictor.stop()
        trader.stop()
        learner.stop()

        await gamma.close()
        await clob.close()
        await db.close()

        await telegram.send_message("⛔ *PolyPoly Bot arrêté*")
        logger.info("PolyPoly arrêté proprement")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Bot arrêté.[/yellow]")
