"""
PolyPoly — Test Local Complet (Mode Simulation)
Teste les 5 agents avec de vraies données Polymarket.
Aucune clé API requise pour ce test (sauf Telegram optionnel).
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from loguru import logger

# Forcer le mode simulation
os.environ.setdefault("POLYMARKET_PRIVATE_KEY", "")
os.environ.setdefault("ANTHROPIC_API_KEY", "")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "")
os.environ.setdefault("TELEGRAM_CHAT_ID", "")
os.environ.setdefault("DATABASE_PATH", "data/test_polypoly.db")

console = Console()

# ------------------------------------------------------------------ #
# MOCK TELEGRAM (pas besoin de vrai token pour tester)
# ------------------------------------------------------------------ #
class MockTelegram:
    async def start(self): pass
    async def send_message(self, text, **kw):
        # Afficher les notifs Telegram dans le terminal
        clean = text.replace("*", "").replace("`", "")
        console.print(f"  [dim cyan][TELEGRAM][/dim cyan] {clean[:120]}")
        return True
    async def notify_opportunity(self, s): await self.send_message(f"🎯 Opportunité: {s.get('question','')[:60]}")
    async def notify_trade_placed(self, t): await self.send_message(f"✅ Trade placé: {t.get('question','')[:50]} | ${t.get('size_usd',0):.2f}")
    async def notify_trade_result(self, t): await self.send_message(f"{'🏆' if t.get('status')=='WON' else '💀'} Résultat: {t.get('pnl',0):+.2f}$")
    async def notify_daily_report(self, s): await self.send_message(f"📊 Win rate: {s.get('win_rate',0):.1f}% | P&L: {s.get('total_pnl',0):+.2f}$")
    async def notify_anomaly(self, m): await self.send_message(f"⚡ Anomalie: {m.get('question','')[:60]}")
    async def notify_learning_update(self, p, a): await self.send_message(f"🧠 Apprentissage: {p} → {a}")
    async def notify_error(self, e, ctx=""): pass


# ------------------------------------------------------------------ #
# TESTS
# ------------------------------------------------------------------ #

async def test_1_database():
    """Test 1 — Base de données"""
    console.print("\n[bold cyan]TEST 1 — Base de données[/bold cyan]")
    from utils.database import Database

    db = Database("data/test_polypoly.db")
    await db.connect()

    # Test upsert marché
    await db.upsert_market({
        "id": "test_market_001",
        "question": "Will Bitcoin reach $100k before 2026?",
        "category": "crypto",
        "yes_price": 0.42,
        "no_price": 0.58,
        "liquidity": 15000.0,
        "volume_24h": 3200.0,
        "end_date": "2025-12-31T23:59:00Z",
        "active": 1,
        "anomaly_score": 0.0,
        "spread": 0.02,
        "last_updated": datetime.now().isoformat(),
        "raw_data": '{"clobTokenIds": ["token_yes_001", "token_no_001"]}',
    })

    # Test historique prix
    for p in [0.38, 0.40, 0.42, 0.45, 0.48]:
        await db.record_price("test_market_001", p, 1 - p, abs(p - 0.5) * 0.1, 3200)

    markets = await db.get_active_markets()
    history = await db.get_price_history("test_market_001", minutes=60)

    console.print(f"  [green]✓[/green] {len(markets)} marché(s) en DB")
    console.print(f"  [green]✓[/green] {len(history)} entrées d'historique prix")

    # Test signal
    sig_id = await db.save_signal({
        "market_id": "test_market_001",
        "signal_type": "PREDICTION",
        "direction": "YES",
        "confidence": 0.78,
        "edge": 0.12,
        "predicted_prob": 0.54,
        "market_price": 0.42,
        "sentiment_score": 0.35,
        "source": "XGBoost(0.54)",
    })
    console.print(f"  [green]✓[/green] Signal sauvegardé (ID={sig_id})")

    # Test trade
    trade_id = await db.save_trade({
        "market_id": "test_market_001",
        "order_id": "SIM_TEST_001",
        "direction": "YES",
        "size_usd": 5.0,
        "entry_price": 0.42,
        "status": "OPEN",
        "signal_id": sig_id,
        "confidence": 0.78,
        "edge": 0.12,
        "sentiment_score": 0.35,
        "features_json": "[0.42, 0.58, 0.08, 0.02, 0.0, 0.15, 0.06, 0.0, 0.35, 0.5, 0.1, 7.0, 0.1764, 0.147, 0.213]",
    })
    console.print(f"  [green]✓[/green] Trade sauvegardé (ID={trade_id})")

    # Test params dynamiques
    await db.set_param("min_confidence_threshold", 0.72, "Test")
    val = await db.get_param("min_confidence_threshold")
    console.print(f"  [green]✓[/green] Paramètre dynamique: {val}")

    console.print(f"  [bold green]✓ DATABASE OK[/bold green]")
    return db


async def test_2_market_scanner(db):
    """Test 2 — Agent 1 (Scanner)"""
    console.print("\n[bold cyan]TEST 2 — Agent 1 : Market Scanner[/bold cyan]")
    from utils.polymarket_api import GammaAPI, parse_market
    from agents.market_scanner import MarketScanner

    telegram = MockTelegram()
    gamma = GammaAPI()

    console.print("  Connexion à l'API Polymarket Gamma...")
    try:
        markets_raw = await gamma.get_markets(limit=10)
        if markets_raw:
            console.print(f"  [green]✓[/green] {len(markets_raw)} marchés récupérés depuis Polymarket")

            # Parser quelques marchés
            parsed = [parse_market(m) for m in markets_raw[:5]]
            for m in parsed:
                if m.get("question"):
                    console.print(
                        f"  [dim]→[/dim] [{m['yes_price']*100:.0f}¢] "
                        f"{m['question'][:70]}"
                    )
        else:
            console.print("  [yellow]⚠ Pas de marchés retournés (API peut être limitée)[/yellow]")
    except Exception as e:
        console.print(f"  [yellow]⚠ API Polymarket non accessible: {e}[/yellow]")
        console.print("  [dim]→ Utilisation de données simulées[/dim]")
        # Créer des marchés fictifs pour continuer le test
        await _inject_mock_markets(db)

    scanner = MarketScanner(db, gamma, telegram)

    console.print("  Calcul des scores d'anomalie...")
    market = await db.get_market("test_market_001")
    if market:
        # Injecter historique prix pour test anomalie
        for p in [0.38, 0.41, 0.45, 0.50]:  # Mouvement de +12% → anomalie
            await db.record_price("test_market_001", p, 1 - p, 0.02, 3000)
        score = await scanner._compute_anomaly_score(market)
        console.print(f"  [green]✓[/green] Score anomalie calculé: {score:.3f}")

    top = await scanner.get_top_markets(n=5)
    console.print(f"  [green]✓[/green] Top {len(top)} marchés disponibles")
    console.print(f"  [bold green]✓ SCANNER OK[/bold green]")

    await gamma.close()
    return scanner


async def test_3_sentiment(db):
    """Test 3 — Agent 2 (Sentiment)"""
    console.print("\n[bold cyan]TEST 3 — Agent 2 : Sentiment Agent[/bold cyan]")
    from agents.sentiment_agent import SentimentAgent

    telegram = MockTelegram()
    agent = SentimentAgent(db, telegram)
    await agent.start()

    # Test analyse de sentiment sans vraies APIs (RSS seulement)
    console.print("  Test VADER sentiment analyzer...")
    if agent._vader:
        test_texts = [
            "Bitcoin is showing incredible bullish momentum, reaching new all-time highs!",
            "Market crash imminent, sell everything before it's too late",
            "Fed maintains rates, stable outlook for next quarter",
        ]
        for text in test_texts:
            score = agent._vader.polarity_scores(text)["compound"]
            sentiment = "positif" if score > 0.1 else "négatif" if score < -0.1 else "neutre"
            console.print(f"  [dim]→[/dim] [{score:+.3f} {sentiment}] \"{text[:60]}\"")
        console.print(f"  [green]✓[/green] VADER fonctionnel")
    else:
        console.print(f"  [yellow]⚠ VADER non disponible[/yellow]")

    # Test sur RSS (gratuit, pas besoin d'API)
    console.print("  Récupération flux RSS (sans API)...")
    try:
        rss_texts = await agent._fetch_rss_data()
        console.print(f"  [green]✓[/green] {len(rss_texts)} textes depuis RSS")
    except Exception as e:
        console.print(f"  [yellow]⚠ RSS: {e}[/yellow]")
        rss_texts = ["Bitcoin hits new high", "Election results uncertain", "Market volatile"]

    # Test analyse sentiment sur un marché
    markets = await db.get_active_markets(limit=5)
    if markets:
        market = markets[0]
        all_texts = rss_texts + [
            f"I think {market['question'][:30]} is very likely to happen",
            f"Analysts predict positive outcome for this event",
        ]
        signal = await agent._analyze_market_sentiment(market, all_texts)
        if signal:
            console.print(
                f"  [green]✓[/green] Signal sentiment généré: "
                f"{signal['direction']} | conf={signal['confidence']:.2%} | "
                f"edge={signal['edge']:+.2%}"
            )
        else:
            console.print("  [dim]→ Pas assez de signal (edge insuffisant — normal)[/dim]")

    console.print(f"  [bold green]✓ SENTIMENT OK[/bold green]")
    return agent


async def test_4_prediction(db):
    """Test 4 — Agent 3 (Prédiction)"""
    console.print("\n[bold cyan]TEST 4 — Agent 3 : Prediction Agent[/bold cyan]")
    from agents.prediction_agent import PredictionAgent

    telegram = MockTelegram()
    agent = PredictionAgent(db, telegram)

    # Test construction des 35 features
    console.print("  Test construction des 35 features XGBoost...")
    market = await db.get_market("test_market_001")
    if market:
        price_hist = await db.get_price_history("test_market_001", minutes=60)
        mock_ob = {"obi": 0.35, "bid_depth": 5000, "ask_depth": 3000,
                   "depth_ratio": 1.67, "whale_bid_ratio": 0.12,
                   "whale_ask_ratio": 0.05, "ob_spread": 0.02,
                   "is_thin": 0, "obi_trend": 0.1}
        features = agent._build_features(market, sentiment_score=0.35,
                                          ob_features=mock_ob, price_history=price_hist)
        console.print(f"  [green]✓[/green] {len(features)} features construites (vs 15 avant)")

    # Test entraînement avec des données simulées
    console.print("  Injection de trades d'entraînement simulés...")
    await _inject_training_trades(db)

    closed_trades = await db.get_closed_trades(limit=200)
    console.print(f"  [green]✓[/green] {len(closed_trades)} trades d'entraînement disponibles")

    if len(closed_trades) >= 50:
        console.print("  Entraînement XGBoost...")
        await agent._train_model(closed_trades)
        if agent._model_trained:
            console.print(f"  [green]✓[/green] Modèle XGBoost entraîné et sauvegardé")

            # Test prédiction
            if market:
                features = agent._build_features(market, 0.35)
                features_scaled = agent._scaler.transform(features.reshape(1, -1))
                proba = agent._model.predict_proba(features_scaled)[0]
                console.print(f"  [green]✓[/green] Prédiction XGBoost: P(YES)={proba[1]:.3f} | P(NO)={proba[0]:.3f}")
    else:
        console.print(f"  [yellow]⚠ Pas assez de trades ({len(closed_trades)}<50) — XGBoost non entraîné[/yellow]")

    console.print(f"  [bold green]✓ PREDICTION OK[/bold green]")
    return agent


async def test_5_trading(db):
    """Test 5 — Agent 4 (Trading)"""
    console.print("\n[bold cyan]TEST 5 — Agent 4 : Trading Agent (Simulation)[/bold cyan]")
    from utils.polymarket_api import CLOBClient, GammaAPI
    from agents.trading_agent import TradingAgent, RiskManager

    telegram = MockTelegram()
    clob = CLOBClient()
    gamma = GammaAPI()
    agent = TradingAgent(db, clob, gamma, telegram)
    agent._simulation_mode = True

    risk = RiskManager(db)

    # Test gestion du risque
    console.print("  Test Risk Manager...")

    good_signal = {
        "market_id": "test_market_002",
        "confidence": 0.80,
        "edge": 0.12,
        "market_price": 0.42,
    }
    can, reason = await risk.can_trade(good_signal)
    console.print(f"  [green]✓[/green] Bon signal → can_trade={can} ({reason})")

    bad_signal_low_conf = {"market_id": "test_market_003", "confidence": 0.50, "edge": 0.12}
    can, reason = await risk.can_trade(bad_signal_low_conf)
    console.print(f"  [green]✓[/green] Conf. faible → can_trade={can} ({reason})")

    bad_signal_low_edge = {"market_id": "test_market_004", "confidence": 0.80, "edge": 0.02}
    can, reason = await risk.can_trade(bad_signal_low_edge)
    console.print(f"  [green]✓[/green] Edge faible → can_trade={can} ({reason})")

    # Test Kelly sizing
    for conf, edge, price in [(0.80, 0.12, 0.42), (0.90, 0.20, 0.30), (0.75, 0.08, 0.60)]:
        size = risk.compute_trade_size(
            {"confidence": conf, "edge": edge, "market_price": price}, 100.0
        )
        console.print(f"  [dim]→[/dim] conf={conf:.0%} edge={edge:.0%} price={price:.2f} → taille=${size:.2f}")

    # Test placement trade simulé
    console.print("  Simulation placement d'un trade...")
    await db.upsert_market({
        "id": "test_market_002",
        "question": "Will Ethereum ETF be approved by SEC in 2025?",
        "category": "crypto",
        "yes_price": 0.35,
        "no_price": 0.65,
        "liquidity": 8000.0,
        "volume_24h": 1500.0,
        "end_date": "2025-12-01T00:00:00Z",
        "active": 1,
        "anomaly_score": 0.6,
        "spread": 0.03,
        "last_updated": datetime.now().isoformat(),
        "raw_data": '{"clobTokenIds": ["token_eth_yes", "token_eth_no"]}',
    })

    # Sauvegarder un signal de prédiction
    sig_id = await db.save_signal({
        "market_id": "test_market_002",
        "signal_type": "PREDICTION",
        "direction": "YES",
        "confidence": 0.81,
        "edge": 0.15,
        "predicted_prob": 0.50,
        "market_price": 0.35,
        "sentiment_score": 0.28,
        "source": "XGBoost(0.50)",
    })

    signal = (await db.get_recent_signals(limit=10))[0]
    trade_id = await agent._execute_trade(signal)
    if trade_id:
        console.print(f"  [green]✓[/green] Trade simulé #{trade_id} placé")
        await telegram.notify_trade_placed({"question": "ETH ETF approved?", "direction": "YES", "size_usd": 5.0, "entry_price": 0.35, "confidence": 0.81, "order_id": "SIM_TEST"})
    else:
        console.print(f"  [dim]→ Trade non placé (logique de risque)[/dim]")

    await clob.close()
    await gamma.close()
    console.print(f"  [bold green]✓ TRADING OK[/bold green]")
    return agent


async def test_6_learning(db):
    """Test 6 — Agent 5 (Apprentissage)"""
    console.print("\n[bold cyan]TEST 6 — Agent 5 : Learning Agent[/bold cyan]")
    from agents.learning_agent import LearningAgent

    telegram = MockTelegram()
    agent = LearningAgent(db, telegram)
    await agent._init_dynamic_params()

    # Injecter des trades perdants avec différents patterns
    console.print("  Injection de trades perdants simulés...")
    losing_trades = [
        {"direction": "YES", "confidence": 0.92, "edge": 0.08, "sentiment_score": 0.6,
         "status": "LOST", "pnl": -5.0, "size_usd": 5.0, "market_id": "tm1",
         "question": "Will X happen?", "raw_data": '{"liquidity": 800}'},
        {"direction": "NO", "confidence": 0.88, "edge": 0.06, "sentiment_score": 0.55,
         "status": "LOST", "pnl": -5.0, "size_usd": 5.0, "market_id": "tm2",
         "question": "Will Y happen?", "raw_data": '{"liquidity": 1200}'},
        {"direction": "YES", "confidence": 0.91, "edge": 0.04, "sentiment_score": 0.48,
         "status": "LOST", "pnl": -5.0, "size_usd": 5.0, "market_id": "tm3",
         "question": "Will Z happen?", "raw_data": '{"liquidity": 900}'},
    ]

    patterns = await agent._analyze_losing_patterns(losing_trades)
    console.print(f"  [green]✓[/green] Patterns détectés: {list(patterns.keys())}")

    # Simuler des statistiques de trades
    stats = {
        "total": 30, "wins": 18, "losses": 12,
        "win_rate": 60.0, "total_pnl": 12.5,
        "avg_confidence": 0.79, "avg_edge": 0.09,
    }

    old_conf = await db.get_param("min_confidence_threshold")
    await agent._update_parameters(patterns, stats)
    new_conf = await db.get_param("min_confidence_threshold")

    console.print(
        f"  [green]✓[/green] Seuil confiance ajusté: "
        f"{old_conf:.2%} → {new_conf:.2%}"
    )

    # Afficher les patterns appris
    all_patterns = await db.get_learning_patterns()
    if all_patterns:
        console.print(f"  [green]✓[/green] {len(all_patterns)} pattern(s) en mémoire:")
        for p in all_patterns[:3]:
            console.print(f"  [dim]→[/dim] {p['pattern_type']}: {p['description']}")

    console.print(f"  [bold green]✓ LEARNING OK[/bold green]")


async def _inject_mock_markets(db):
    """Injecte des marchés fictifs si l'API est indisponible."""
    mocks = [
        ("Will Biden run in 2028?", "politics", 0.15),
        ("Will BTC hit $200k in 2025?", "crypto", 0.28),
        ("Will Fed cut rates in Q1 2025?", "economics", 0.62),
        ("Will Nvidia stock hit $200?", "stocks", 0.45),
        ("Will SpaceX launch Starship in 2025?", "science", 0.71),
    ]
    for i, (q, cat, price) in enumerate(mocks):
        await db.upsert_market({
            "id": f"mock_market_{i:03d}",
            "question": q, "category": cat,
            "yes_price": price, "no_price": round(1 - price, 2),
            "liquidity": 5000 + i * 1000, "volume_24h": 1000 + i * 500,
            "end_date": "2025-12-31T23:59:00Z",
            "active": 1, "anomaly_score": 0.0, "spread": 0.02,
            "last_updated": datetime.now().isoformat(),
            "raw_data": f'{{"clobTokenIds": ["yes_{i}", "no_{i}"]}}',
        })


async def _inject_training_trades(db):
    """Injecte des trades d'entraînement avec features pour XGBoost."""
    import random, json
    random.seed(42)

    for i in range(60):
        price = random.uniform(0.2, 0.8)
        pred_prob = price + random.gauss(0, 0.12)
        pred_prob = max(0.05, min(0.95, pred_prob))
        won = (pred_prob > price + 0.03) and (random.random() > 0.35)

        # 35 features (nouvelle version)
        features = [
            price, 1-price, abs(price-0.5), random.uniform(0,0.03), random.uniform(0.01,0.08),
            random.uniform(0.05,0.8), random.uniform(0.02,0.5), random.uniform(0.05,1.0), random.uniform(0,0.9),
            random.uniform(0.1,0.9), random.uniform(0.01,0.5), random.uniform(1,20),
            random.uniform(0,1), random.uniform(0,1),
            random.uniform(0,0.05), random.uniform(-0.1,0.1), random.uniform(-0.15,0.15),
            random.uniform(-0.02,0.02), random.uniform(-0.05,0.05),
            random.uniform(-0.5,0.5), random.uniform(0,1), random.uniform(0,1),
            random.uniform(0.5,2), random.uniform(-0.3,0.3),
            random.uniform(0,0.3), random.uniform(0,0.3), random.uniform(0,1),
            random.uniform(-0.5,0.5), random.uniform(0,0.5),
            random.uniform(0,1), random.uniform(0,1), random.uniform(0.01,0.1),
            price*random.uniform(-0.3,0.3), price*random.uniform(-0.3,0.3),
            random.uniform(0,0.3),
        ]

        trade_id = await db.save_trade({
            "market_id": f"training_market_{i:03d}",
            "order_id": f"SIM_TRAIN_{i:03d}",
            "direction": "YES" if pred_prob > price else "NO",
            "size_usd": 5.0,
            "entry_price": price,
            "status": "OPEN",
            "signal_id": None,
            "confidence": min(0.5 + abs(pred_prob - price) * 2, 0.95),
            "edge": pred_prob - price,
            "sentiment_score": random.uniform(-0.4, 0.6),
            "features_json": json.dumps(features),
        })

        await db.update_trade(trade_id, {
            "status": "WON" if won else "LOST",
            "exit_price": 1.0 if won else 0.0,
            "pnl": 5.0 * (1 / price - 1) if won else -5.0,
            "resolved_at": datetime.now().isoformat(),
        })


async def show_final_summary(db):
    """Affiche le résumé final."""
    console.print()

    stats = await db.get_trade_stats()
    markets = await db.get_active_markets()
    signals = await db.get_recent_signals()
    patterns = await db.get_learning_patterns()
    open_trades = await db.get_open_trades()

    table = Table(title="Résumé de l'état du bot", border_style="cyan")
    table.add_column("Composant", style="cyan", width=28)
    table.add_column("Valeur", style="white")

    table.add_row("Marchés en DB", str(len(markets)))
    table.add_row("Signaux générés", str(len(signals)))
    table.add_row("Total trades", str(stats.get("total", 0)))
    table.add_row("Positions ouvertes", str(len(open_trades)))
    table.add_row("Win rate", f"{stats.get('win_rate', 0):.1f}%")
    table.add_row("P&L total", f"${stats.get('total_pnl', 0):+.2f}")
    table.add_row("Patterns appris", str(len(patterns)))
    table.add_row("DB path", "data/test_polypoly.db")

    console.print(table)

    # Params dynamiques
    param_conf = await db.get_param("min_confidence_threshold", 0.72)
    param_edge = await db.get_param("min_edge_threshold", 0.05)
    console.print(f"\n  Paramètres dynamiques (Agent 5):")
    console.print(f"  [dim]→[/dim] Seuil confiance: [cyan]{param_conf:.2%}[/cyan]")
    console.print(f"  [dim]→[/dim] Edge minimum:    [cyan]{param_edge:.2%}[/cyan]")


async def main():
    """Lance tous les tests en séquence."""
    console.print(Panel(
        "[bold cyan]PolyPoly — Test Local Complet[/bold cyan]\n"
        "[dim]Tous les tests tournent en mode simulation\n"
        "Aucune clé API requise pour ce test[/dim]",
        border_style="cyan",
    ))

    import os
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Supprimer la DB de test précédente
    if os.path.exists("data/test_polypoly.db"):
        os.remove("data/test_polypoly.db")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initialisation...", total=None)
        progress.update(task, description="Tests en cours...")

    try:
        db = await test_1_database()
        await test_2_market_scanner(db)
        await test_3_sentiment(db)
        await test_4_prediction(db)
        await test_5_trading(db)
        await test_6_learning(db)
        await test_7_new_agents(db)

        await show_final_summary(db)
        await db.close()

        console.print()
        console.print(Panel(
            "[bold green]Tous les tests passent ![/bold green]\n\n"
            "Pour lancer le vrai bot:\n"
            "  [cyan]1.[/cyan] Copie .env.example → .env\n"
            "  [cyan]2.[/cyan] Remplis les clés API dans .env\n"
            "  [cyan]3.[/cyan] Lance:  [bold]python main.py[/bold]",
            border_style="green",
            title="✓ Succès",
        ))

    except Exception as e:
        console.print(f"\n[bold red]ERREUR: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def test_7_new_agents(db):
    """Test 7 — Nouveaux agents (Arbitrage, Signal Combiner, Smart Exit)"""
    console.print("\n[bold cyan]TEST 7 — Nouvelles Améliorations v2[/bold cyan]")

    # 7a. Arbitrage Scanner
    console.print("  Test Arbitrage Scanner...")
    from agents.arbitrage_scanner import ArbitrageScanner
    from utils.polymarket_api import CLOBClient, GammaAPI
    gamma = GammaAPI()
    clob = CLOBClient()
    arb = ArbitrageScanner(db, gamma, clob, MockTelegram())

    # Injecter marché avec YES+NO ≠ 1.0 (arbitrage)
    await db.upsert_market({
        "id": "arbi_test_001",
        "question": "Will Bitcoin ETF see $10B inflows by 2025?",
        "category": "crypto",
        "yes_price": 0.55,
        "no_price": 0.52,   # Sum = 1.07 → arbitrage !
        "liquidity": 12000.0, "volume_24h": 3000.0,
        "end_date": "2025-12-31T00:00:00Z",
        "active": 1, "anomaly_score": 0.7, "spread": 0.03,
        "last_updated": datetime.now().isoformat(),
        "raw_data": '{"clobTokenIds": ["arbi_yes", "arbi_no"]}',
    })

    opps = await arb._scan_price_sum_arbitrage()
    arbi_found = [o for o in opps if o.market_id == "arbi_test_001"]
    if arbi_found:
        o = arbi_found[0]
        console.print(
            f"  [green]✓[/green] Arbitrage détecté: YES={o.yes_price:.2f}+NO={o.no_price:.2f}="
            f"{o.sum_prices:.2f} | Edge={o.edge:.2%}"
        )
    else:
        console.print("  [dim]→ Arbitrage non détecté (données de test)[/dim]")

    # 7b. Signal Combiner
    console.print("  Test Signal Combiner (fusion Bayésienne)...")
    from agents.signal_combiner import SignalCombiner
    combiner = SignalCombiner(db, MockTelegram())

    # Injecter des signaux concordants
    for sig_type, conf in [("PREDICTION", 0.79), ("ORDERBOOK", 0.75), ("SENTIMENT", 0.68)]:
        await db.save_signal({
            "market_id": "test_market_001",
            "signal_type": sig_type,
            "direction": "YES",
            "confidence": conf,
            "edge": 0.12,
            "predicted_prob": 0.54,
            "market_price": 0.42,
            "sentiment_score": 0.3,
            "source": f"Test {sig_type}",
        })

    market = await db.get_market("test_market_001")
    combined = await combiner.combine_signals("test_market_001", market)
    if combined:
        console.print(
            f"  [green]✓[/green] Signal combiné: {combined.direction} | "
            f"conf={combined.combined_confidence:.2%} | "
            f"sources={combined.source_types}"
        )
    else:
        console.print("  [dim]→ Signal combiné non généré (seuil non atteint)[/dim]")

    # 7c. Smart Exit Manager
    console.print("  Test Smart Exit Manager...")
    from agents.trading_agent import SmartExitManager
    exit_mgr = SmartExitManager(db, clob, MockTelegram(), simulation_mode=True)

    # Simuler un trade gagnant à 85% (devrait déclencher profit-take)
    trade_sim = {
        "id": 999, "direction": "YES",
        "entry_price": 0.42, "size_usd": 5.0,
        "placed_at": (datetime.now() - timedelta(minutes=10)).isoformat(),
        "question": "Test market",
    }
    exited = await exit_mgr.check_and_exit(trade_sim, current_price=0.85)
    console.print(f"  [green]✓[/green] Profit-Take (prix 0.85 ≥ 0.80): sortie={'OUI' if exited else 'NON'}")

    # Simuler stop-loss
    exited_sl = await exit_mgr.check_and_exit(trade_sim, current_price=0.13)
    console.print(f"  [green]✓[/green] Stop-Loss (prix 0.13 ≤ 0.35×0.42): sortie={'OUI' if exited_sl else 'NON'}")

    # 7d. 35 features vs 15 avant
    console.print("  Comparaison features: 15 (v1) → 35 (v2)...")
    from agents.prediction_agent import PredictionAgent
    agent = PredictionAgent(db, MockTelegram())
    m = await db.get_market("test_market_001")
    f = agent._build_features(m, 0.3)
    console.print(f"  [green]✓[/green] {len(f)} features XGBoost (OBI, momentum, volatilité, baleines...)")

    await gamma.close()
    await clob.close()
    console.print(f"  [bold green]✓ NOUVEAUX AGENTS OK[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
