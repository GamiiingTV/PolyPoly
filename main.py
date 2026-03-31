"""
PolyPoly — Orchestrateur Principal v2
Lance et coordonne les 7 agents IA en parallèle.
AMÉLIORATIONS : OrderBook, Arbitrage, Signal Combiner, WebSocket, Smart Exits.
"""

import asyncio
import sys
from datetime import datetime, timedelta
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
from agents.llm_validator        import LLMValidator
from agents.metaculus_agent      import MetaculusAgent
from agents.whale_tracker        import WhaleTracker
from agents.cross_platform_agent import CrossPlatformAgent
from agents.wikipedia_agent      import WikipediaAgent
from agents.bookmaker_agent      import BookmakerAgent
from agents.news_flash_agent     import NewsFlashAgent
from agents.smart_money_agent    import SmartMoneyAgent

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
    table.add_row("Cross-Platform", "[green]✓ Manifold vs Polymarket[/green]")
    table.add_row("Wikipedia Monitor", "[green]✓ Éditions temps réel[/green]")
    table.add_row("Bookmaker Odds", "[green]✓[/green]" if config.ODDS_API_KEY else "[yellow]✗ (ODDS_API_KEY manquant)[/yellow]")
    table.add_row("News Flash", "[green]✓ Breaking news → marchés[/green]")
    table.add_row("Smart Money", "[green]✓ Copy trading gros wallets[/green]")
    table.add_row("XGBoost historique", "[green]✓ Pré-entraîné au démarrage[/green]")
    table.add_row("Cohérence inter-marchés", "[green]✓[/green]")
    table.add_row("Vélocité news", "[green]✓[/green]")
    table.add_row("Calibration catégorie", "[green]✓[/green]")
    table.add_row("Événements planifiés", "[green]✓[/green]")
    table.add_row("Smart Exits", "[green]✓ (TP 80% / SL 35% / Trail 30%)[/green]")
    console.print(table)
    console.print()


async def daily_report_task(db: Database, telegram) -> None:
    """Rapport quotidien envoyé chaque matin à 8h UTC."""
    while True:
        now = datetime.utcnow()
        # Prochaine occurrence de 8h UTC
        next_run = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run = next_run + timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())

        try:
            stats = await db.get_trade_stats()
            signals = await db.get_recent_signals(limit=200)
            open_trades = await db.get_open_trades()

            # Top 5 opportunités par edge
            top_signals = sorted(
                [s for s in signals if abs(s.get("edge", 0)) > 0.05],
                key=lambda x: abs(x.get("edge", 0)),
                reverse=True,
            )[:5]

            total = stats.get("total", 0)
            wins = stats.get("wins", 0)
            win_rate = stats.get("win_rate", 0)
            total_pnl = stats.get("total_pnl", 0)
            pnl_str = f"+${total_pnl:.2f}" if total_pnl >= 0 else f"-${abs(total_pnl):.2f}"

            lines = [
                "📊 <b>RAPPORT QUOTIDIEN — PolyPoly</b>",
                f"📅 {datetime.utcnow().strftime('%d/%m/%Y')}",
                "═══════════════════",
                f"🏆 Win rate: <b>{win_rate:.1f}%</b>  ({wins}W / {total - wins}L)",
                f"💵 P&amp;L total: <code>{pnl_str}</code>",
                f"📈 Trades: {total} total | {len(open_trades)} ouverts",
                "",
                "🎯 <b>Top 5 opportunités (24h)</b>",
            ]

            if top_signals:
                for i, sig in enumerate(top_signals, 1):
                    direction = sig.get("direction", "?")
                    edge = sig.get("edge", 0) * 100
                    conf = sig.get("confidence", 0) * 100
                    q = sig.get("question", "")[:55]
                    emoji = "🟢" if direction == "YES" else "🔴"
                    lines.append(
                        f"{i}. {emoji} {q}\n"
                        f"   Edge: <b>{edge:+.1f}%</b> | Conf: {conf:.0f}%"
                    )
            else:
                lines.append("Aucun signal fort hier.")

            await telegram.send_message("\n".join(lines))
        except Exception as e:
            logger.error(f"Daily report erreur: {e}")


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


async def supervised_task(coro_fn, name: str, restart_delay: float = 5.0):
    """
    Superviseur par tâche : si un agent crash, on le relance automatiquement
    au lieu de tuer tout le bot.
    """
    while True:
        try:
            await coro_fn()
        except asyncio.CancelledError:
            logger.info(f"{name} annulé proprement")
            return
        except Exception as e:
            logger.error(f"{name} a crashé: {e} — relance dans {restart_delay}s")
            await asyncio.sleep(restart_delay)


async def main() -> None:
    setup_logging()
    print_banner()

    # --- Services partagés ---
    db = Database(config.DATABASE_PATH)
    await db.connect()

    gamma = GammaAPI()
    clob = CLOBClient()

    # --- Telegram (lazy import pour compatibilité) ---
    class _NoOpTelegram:
        async def start(self): pass
        async def stop(self): pass
        async def send_message(self, *a, **k): pass
        async def notify_opportunity(self, *a): pass
        async def notify_trade_placed(self, *a): pass
        async def notify_trade_result(self, *a): pass
        async def notify_daily_report(self, *a): pass
        async def notify_anomaly(self, *a): pass
        async def notify_learning_update(self, *a): pass
        async def notify_error(self, *a, **k): pass
        async def notify_news_flash(self, *a, **k): pass

    try:
        from utils.telegram_bot import TelegramNotifier
        telegram = TelegramNotifier()
        await telegram.start()
    except BaseException as _e:
        telegram = _NoOpTelegram()
        logger.warning(f"Telegram désactivé: {_e}")

    # --- Agents 8, 9 (pas de boucle infinie, utilisés par d'autres agents) ---
    try:
        llm_validator = LLMValidator()
        await llm_validator.start()
    except Exception as e:
        logger.error(f"LLMValidator init échoué (non bloquant): {e}")
        class _NoOpValidator:
            def stop(self): pass
            async def validate_signal(self, *a, **k): return None
            def record_outcome(self, *a, **k): pass
        llm_validator = _NoOpValidator()

    try:
        metaculus = MetaculusAgent()
    except Exception as e:
        logger.error(f"MetaculusAgent init échoué: {e}")
        metaculus = None

    # --- Agents principaux — chaque instanciation protégée ---
    try:
        ob_agent = OrderBookAgent(db, clob, gamma, telegram)
    except Exception as e:
        logger.error(f"OrderBookAgent init échoué: {e}"); ob_agent = None

    scanner   = MarketScanner(db, gamma, telegram)
    sentiment = SentimentAgent(db, telegram,
                               llm_validator=llm_validator,
                               metaculus=metaculus)
    predictor = PredictionAgent(db, telegram, ob_agent=ob_agent)
    combiner  = SignalCombiner(db, telegram)
    trader    = TradingAgent(db, clob, gamma, telegram)
    learner   = LearningAgent(db, telegram, llm_validator=llm_validator)
    arb        = ArbitrageScanner(db, gamma, clob, telegram)

    try:
        whale = WhaleTracker(db, gamma, clob)
    except Exception as e:
        logger.error(f"WhaleTracker init échoué: {e}"); whale = None

    try:
        cross_plat = CrossPlatformAgent(db, telegram)
    except Exception as e:
        logger.error(f"CrossPlatformAgent init échoué: {e}"); cross_plat = None

    try:
        wiki = WikipediaAgent(db, telegram)
    except Exception as e:
        logger.error(f"WikipediaAgent init échoué: {e}"); wiki = None

    try:
        bookmaker = BookmakerAgent(db, telegram)
    except Exception as e:
        logger.error(f"BookmakerAgent init échoué: {e}"); bookmaker = None

    try:
        news_flash = NewsFlashAgent(db, telegram)
    except Exception as e:
        logger.error(f"NewsFlashAgent init échoué: {e}"); news_flash = None

    try:
        smart_money = SmartMoneyAgent(db, telegram)
    except Exception as e:
        logger.error(f"SmartMoneyAgent init échoué: {e}"); smart_money = None

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
    try:
        await scanner.scan_cycle()
    except Exception as e:
        logger.warning(f"Scan initial échoué (non bloquant): {e}")

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

    # --- Lancer tous les agents avec superviseur (crash d'un agent ≠ mort du bot) ---
    def _task(agent, name):
        """Crée une tâche supervisée seulement si l'agent a été instancié."""
        if agent is None:
            return None
        return asyncio.create_task(supervised_task(agent.run_forever, name), name=name)

    tasks = [t for t in [
        _task(scanner,    "Agent1-Scanner"),
        _task(sentiment,  "Agent2-Sentiment"),
        _task(predictor,  "Agent3-Prediction"),
        _task(trader,     "Agent4-Trading"),
        _task(learner,    "Agent5-Learning"),
        _task(ob_agent,   "Agent6-OrderBook"),
        _task(arb,        "Agent7-Arbitrage"),
        _task(feed,       "RealtimeFeed"),
        _task(whale,      "Agent10-Whale"),
        _task(cross_plat, "Agent11-CrossPlatform"),
        _task(wiki,       "Agent12-Wikipedia"),
        _task(bookmaker,  "Agent13-Bookmaker"),
        _task(news_flash, "Agent14-NewsFlash"),
        _task(smart_money,"Agent15-SmartMoney"),
        _task(combiner,   "SignalCombiner"),
        asyncio.create_task(health_check(db),                name="HealthCheck"),
        asyncio.create_task(daily_report_task(db, telegram), name="DailyReport"),
    ] if t is not None]

    console.print("[bold green]15 agents opérationnels — News Flash + Smart Money + XGBoost pré-entraîné[/bold green]\n")
    logger.info("PolyPoly v2 opérationnel")

    try:
        await asyncio.gather(*tasks)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        logger.info("Arrêt en cours...")
        for task in tasks:
            task.cancel()
        for agent in [scanner, sentiment, predictor, trader, learner,
                      ob_agent, arb, feed, whale, llm_validator, metaculus,
                      cross_plat, wiki, bookmaker, news_flash, smart_money, combiner]:
            try:
                if agent is not None:
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
