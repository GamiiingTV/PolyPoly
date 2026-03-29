"""
PolyPoly — Orchestrateur Principal v2
Lance et coordonne les 7 agents IA en parallèle.
AMÉLIORATIONS : OrderBook, Arbitrage, Signal Combiner, WebSocket, Smart Exits.
"""

import asyncio
import sys
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

import config
from utils.database import Database
from utils.polymarket_api import GammaAPI, CLOBClient
from utils.websocket_feed import RealtimeFeed, FallbackPollingFeed

from agents.market_scanner   import MarketScanner
from agents.sentiment_agent  import SentimentAgent
from agents.prediction_agent import PredictionAgent
from agents.trading_agent    import TradingAgent
from agents.learning_agent   import LearningAgent
from agents.orderbook_agent  import OrderBookAgent
from agents.arbitrage_scanner import ArbitrageScanner
from agents.signal_combiner  import SignalCombiner

console = Console()


def setup_logging() -> None:
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
    console.print(Panel(
        "[bold cyan]PolyPoly v2[/bold cyan] [dim]— Polymarket AI Trading Bot[/dim]\n"
        "[dim white]7 Agents IA • XGBoost 35-features • OrderBook • Arbitrage • Smart Exits[/dim white]\n"
        f"[dim green]Démarré: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}[/dim green]",
        border_style="cyan", padding=(1, 4),
    ))

    sim_mode = not bool(
        config.POLYMARKET_PRIVATE_KEY.replace("0xTON_PRIVATE_KEY_POLYGON_WALLET", "")
    )

    table = Table(box=None, show_header=False, padding=(0, 2))
    table.add_column(style="dim white", width=24)
    table.add_column(style="cyan")
    table.add_row("Mode", "[yellow]SIMULATION[/yellow]" if sim_mode else "[bold green]LIVE[/bold green]")
    table.add_row("Max trade", f"${config.MAX_TRADE_SIZE_USD}")
    table.add_row("Confiance min", f"{config.MIN_CONFIDENCE_THRESHOLD:.0%}")
    table.add_row("Edge min", f"{config.MIN_EDGE_THRESHOLD:.0%}")
    table.add_row("Kill switch", f"${config.DAILY_LOSS_LIMIT_USD}/jour" if hasattr(config, 'DAILY_LOSS_LIMIT_USD') else "$15/jour")
    table.add_row("Marchés cibles", str(config.TARGET_MARKETS_COUNT))
    table.add_row("Telegram", "[green]✓[/green]" if config.TELEGRAM_BOT_TOKEN else "[red]✗[/red]")
    table.add_row("LLM Claude", "[green]✓[/green]" if config.ANTHROPIC_API_KEY else "[dim]✗[/dim]")
    table.add_row("WebSocket", "[green]✓[/green]")
    table.add_row("OrderBook", "[green]✓[/green]")
    table.add_row("Arbitrage", "[green]✓[/green]")
    table.add_row("Smart Exits", "[green]✓ (TP 80% / SL 35% / Trail 30%)[/green]")
    console.print(table)
    console.print()


async def health_check(db: Database) -> None:
    """Rapport de santé toutes les heures."""
    while True:
        await asyncio.sleep(3600)
        try:
            stats = await db.get_trade_stats()
            markets = await db.get_active_markets(limit=1000)
            open_trades = await db.get_open_trades()
            patterns = await db.get_learning_patterns()
            best_cat = await db.get_param("best_category", "N/A")

            logger.info(
                f"[HEALTH] {len(markets)} marchés | "
                f"{len(open_trades)} positions | "
                f"WR: {stats.get('win_rate', 0):.1f}% | "
                f"P&L: {stats.get('total_pnl', 0):+.2f}$ | "
                f"{len(patterns)} patterns | "
                f"Top cat: {best_cat}"
            )
        except Exception as e:
            logger.error(f"Health check: {e}")


async def realtime_price_handler(update, db: Database,
                                  scanner: MarketScanner) -> None:
    """
    Callback pour les updates de prix WebSocket.
    Déclenche un re-scan immédiat sur les marchés avec mouvement important.
    """
    if abs(update.price_change) > 0.05:  # Mouvement >5% → re-scan immédiat
        market = await db.get_market(update.market_id)
        if market:
            logger.info(
                f"⚡ Mouvement {update.price_change:+.1%} sur "
                f"{market.get('question', '')[:50]}"
            )
            # Recalculer le score d'anomalie immédiatement
            anomaly = await scanner._compute_anomaly_score(market)
            if anomaly > 0.6:
                await db.upsert_market({**market, "anomaly_score": anomaly})


async def main() -> None:
    setup_logging()
    print_banner()

    # --- Services partagés ---
    db = Database(config.DATABASE_PATH)
    await db.connect()

    gamma = GammaAPI()
    clob = CLOBClient()

    # --- Telegram (lazy import pour compatibilité) ---
    try:
        from utils.telegram_bot import TelegramNotifier
        telegram = TelegramNotifier()
        await telegram.start()
    except BaseException:
        class _NoOpTelegram:
            async def start(self): pass
            async def send_message(self, *a, **k): pass
            async def notify_opportunity(self, *a): pass
            async def notify_trade_placed(self, *a): pass
            async def notify_trade_result(self, *a): pass
            async def notify_daily_report(self, *a): pass
            async def notify_anomaly(self, *a): pass
            async def notify_learning_update(self, *a): pass
            async def notify_error(self, *a, **k): pass
        telegram = _NoOpTelegram()
        logger.warning("Telegram désactivé (dépendance indisponible)")

    # --- 7 Agents ---
    # Agent 6 doit être instancié avant Agent 3 (qui en dépend)
    ob_agent  = OrderBookAgent(db, clob, gamma, telegram)
    scanner   = MarketScanner(db, gamma, telegram)
    sentiment = SentimentAgent(db, telegram)
    predictor = PredictionAgent(db, telegram, ob_agent=ob_agent)   # ← ob_agent injecté
    combiner  = SignalCombiner(db, telegram)
    trader    = TradingAgent(db, clob, gamma, telegram)
    learner   = LearningAgent(db, telegram)
    arb       = ArbitrageScanner(db, gamma, clob, telegram)

    # --- Feed temps réel ---
    try:
        import websockets
        feed = RealtimeFeed(db)
    except ImportError:
        feed = FallbackPollingFeed(db, gamma)

    feed.add_callback(
        lambda upd: realtime_price_handler(upd, db, scanner)
    )

    # --- Scan initial ---
    logger.info("Scan initial des marchés...")
    await scanner.scan_cycle()

    # --- Souscription WebSocket aux marchés récupérés ---
    if isinstance(feed, RealtimeFeed):
        markets = await db.get_active_markets(limit=100)
        import json
        token_ids = []
        for m in markets:
            raw = json.loads(m.get("raw_data", "{}"))
            token_ids.extend(raw.get("clobTokenIds", []))
        if token_ids:
            await feed.subscribe_markets(token_ids[:200])

    # --- Lancer tous les agents en parallèle ---
    tasks = [
        asyncio.create_task(scanner.run_forever(),    name="Agent1-Scanner"),
        asyncio.create_task(sentiment.run_forever(),  name="Agent2-Sentiment"),
        asyncio.create_task(predictor.run_forever(),  name="Agent3-Prediction"),
        asyncio.create_task(trader.run_forever(),     name="Agent4-Trading"),
        asyncio.create_task(learner.run_forever(),    name="Agent5-Learning"),
        asyncio.create_task(ob_agent.run_forever(),   name="Agent6-OrderBook"),
        asyncio.create_task(arb.run_forever(),        name="Agent7-Arbitrage"),
        asyncio.create_task(feed.run_forever(),       name="RealtimeFeed"),
        asyncio.create_task(health_check(db),         name="HealthCheck"),
    ]

    console.print("[bold green]7 agents opérationnels — Feed temps réel actif[/bold green]\n")
    logger.info("PolyPoly v2 opérationnel")

    try:
        await asyncio.gather(*tasks)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        logger.info("Arrêt en cours...")
        for task in tasks:
            task.cancel()
        for agent in [scanner, sentiment, predictor, trader, learner, ob_agent, arb, feed]:
            try:
                agent.stop()
            except Exception:
                pass
        await gamma.close()
        await clob.close()
        await db.close()
        try:
            await telegram.send_message("⛔ *PolyPoly v2 arrêté*")
        except Exception:
            pass
        logger.info("PolyPoly arrêté proprement")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Bot arrêté.[/yellow]")
