#!/usr/bin/env python3
"""
Simulation HFT en direct — données réelles Binance + Polymarket.

Ce script :
1. Récupère les 200 dernières bougies 5M BTC/USDT depuis Binance REST
2. Cherche les marchés BTC 5M actifs sur Polymarket
3. Rejoue le pipeline complet bougie par bougie
4. Simule les trades qu'on aurait passés
5. Calcule le P&L simulé

Les trades sont simulés ainsi :
  - Si signal BULL  → on achète YES à prix_polymarket_actuel
  - Résolution au prix de la bougie suivante (BTC +/- en 5min)
  - P&L = (valeur_resolue - prix_entree) * taille / prix_entree
"""

import asyncio
import json
import sys
import time
from datetime import datetime, timezone

import httpx
import numpy as np

sys.path.insert(0, ".")

from hft.signals.indicators import IndicatorEngine
from hft.signals.force_graph import ForceGraph
from hft.signals.aggregator import SignalAggregator
from hft.signals.tradingview_signals import TradingViewSignals, TVSignals
from hft.feeds.cryptoquant_feed import ExchangeFlowData
from hft.config_hft import (
    CAPITAL_USD,
    FORCE_GRAPH_CONVERGENCE_THRESHOLD,
    RISK_PER_TRADE_USD,
    MIN_EDGE_PCT,
)

BINANCE_REST = "https://api.binance.com"
GAMMA_API    = "https://gamma-api.polymarket.com"

RESET  = "\033[0m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"

def color(text, c): return f"{c}{text}{RESET}"


# ─── Fetch bougies Binance ────────────────────────────────────────────────────

async def fetch_binance_candles(n=200):
    async with httpx.AsyncClient(timeout=15.0) as c:
        r = await c.get(f"{BINANCE_REST}/api/v3/klines",
                        params={"symbol": "BTCUSDT", "interval": "5m", "limit": n})
        r.raise_for_status()
        candles = []
        for k in r.json():
            candles.append({
                "time_ms": int(k[0]),
                "open":    float(k[1]),
                "high":    float(k[2]),
                "low":     float(k[3]),
                "close":   float(k[4]),
                "volume":  float(k[5]),
                "tbv":     float(k[9]),   # taker buy volume
            })
        return candles


# ─── Fetch prix BTC actuel ────────────────────────────────────────────────────

async def fetch_btc_price():
    async with httpx.AsyncClient(timeout=5.0) as c:
        r = await c.get(f"{BINANCE_REST}/api/v3/ticker/price", params={"symbol": "BTCUSDT"})
        return float(r.json()["price"])


# ─── Fetch marchés Polymarket ─────────────────────────────────────────────────

async def fetch_poly_btc_markets():
    btc_kw = ["btc", "bitcoin", "will btc", "higher", "lower", "5 min"]
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get(f"{GAMMA_API}/markets",
                            params={"active": "true", "closed": "false",
                                    "limit": 200, "order": "volume24hr"})
            r.raise_for_status()
            markets = r.json()
            if isinstance(markets, dict):
                markets = markets.get("markets", [])

        found = []
        for m in markets:
            q = (m.get("question") or "").lower()
            if any(kw in q for kw in btc_kw):
                prices = m.get("outcomePrices", [])
                if isinstance(prices, str):
                    try: prices = json.loads(prices)
                    except: prices = []
                yes_price = float(prices[0]) if prices else 0.5
                found.append({
                    "id":          m.get("id",""),
                    "question":    m.get("question","")[:70],
                    "yes_price":   yes_price,
                    "liquidity":   float(m.get("liquidity", 0) or 0),
                    "volume_24h":  float(m.get("volume24hr", 0) or 0),
                    "token_ids":   m.get("clobTokenIds", []),
                })
        return sorted(found, key=lambda x: -x["liquidity"])
    except Exception as e:
        print(color(f"  ⚠ Polymarket: {e}", YELLOW))
        return []


# ─── Simulation principale ────────────────────────────────────────────────────

async def run_simulation():
    print()
    print(color("═" * 65, CYAN))
    print(color("  HFT BTC Polymarket — SIMULATION EN DIRECT", BOLD))
    print(color(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC", CYAN))
    print(color("═" * 65, CYAN))
    print()

    # ── Récupérer les données ────────────────────────────────────────────────
    print("Chargement des données...")

    candles_task    = fetch_binance_candles(200)
    btc_price_task  = fetch_btc_price()
    poly_task       = fetch_poly_btc_markets()

    candles, btc_now, poly_markets = await asyncio.gather(
        candles_task, btc_price_task, poly_task
    )

    print(f"  ✓ {len(candles)} bougies 5M BTC chargées (Binance)")
    print(f"  ✓ Prix BTC actuel : {color(f'${btc_now:,.2f}', BOLD)}")
    if poly_markets:
        best = poly_markets[0]
        print(f"  ✓ Marché Polymarket : {best['question']}")
        print(f"    YES={best['yes_price']:.4f}  Liq=${best['liquidity']:,.0f}  Vol24h=${best['volume_24h']:,.0f}")
    else:
        print(color("  ⚠ Aucun marché BTC actif trouvé sur Polymarket", YELLOW))
    print()

    # ── Signaux TradingView (optionnel) ──────────────────────────────────────
    tv_signals = TVSignals()
    try:
        tv = TradingViewSignals()
        print("Récupération signaux TradingView 5M...")
        await tv._fetch()
        tv_signals = tv.get_latest()
        if tv_signals.fresh:
            reco_map = {1.0: "STRONG BUY", 0.5: "BUY", 0.0: "NEUTRAL",
                        -0.5: "SELL", -1.0: "STRONG SELL"}
            reco_str = reco_map.get(tv_signals.recommendation, f"{tv_signals.recommendation:.1f}")
            print(f"  ✓ TradingView : {color(reco_str, GREEN if tv_signals.recommendation > 0 else RED)} "
                  f"(B={tv_signals.buy_count} S={tv_signals.sell_count} N={tv_signals.neutral_count})")
        else:
            print(color("  ○ TradingView: indisponible (fallback zéro)", YELLOW))
    except Exception as e:
        print(color(f"  ○ TradingView: {e}", YELLOW))
    print()

    # ── Simulation bougie par bougie ─────────────────────────────────────────
    print(color("─" * 65, CYAN))
    print(color("  REPLAY BOUGIES 5M — 100 dernières (=8h30)", BOLD))
    print(color("─" * 65, CYAN))
    print(f"  {'Heure':<8} {'Close':>10} {'RSI':>6} {'MACD':>7} "
          f"{'ForceGraph':>12} {'Seuil':>6} {'Signal':>8} {'P&L sim':>9}")
    print(f"  {'─'*8} {'─'*10} {'─'*6} {'─'*7} {'─'*12} {'─'*6} {'─'*8} {'─'*9}")

    engine    = IndicatorEngine()
    graph     = ForceGraph()
    aggregator = SignalAggregator()
    cq_data   = ExchangeFlowData()  # neutre (pas de clé CryptoQuant en démo)

    # On garde 60 bougies de warmup, on rejoue les 100 suivantes
    warmup  = 60
    replay  = candles[warmup:-1]    # on garde la dernière bougie pour résolution

    trades  = []
    capital = CAPITAL_USD

    for i, candle in enumerate(replay):
        # Fenêtre glissante pour les indicateurs
        window_end = warmup + i + 1
        window     = candles[:window_end]

        opens   = [c["open"]   for c in window]
        highs   = [c["high"]   for c in window]
        lows    = [c["low"]    for c in window]
        closes  = [c["close"]  for c in window]
        volumes = [c["volume"] for c in window]

        ind      = engine.compute(opens, highs, lows, closes, volumes)
        ind_sigs = engine.normalize(ind)

        # Estimer le "prix Polymarket" simulé
        # Dans la réalité c'est le prix CLOB en temps réel
        # En simu : on utilise la probabilité empirique basée sur momentum
        momentum = (closes[-1] - closes[-6]) / closes[-6] if closes[-6] else 0
        import math
        simulated_poly_yes = 0.5 + math.tanh(momentum / 0.004) * 0.12
        simulated_poly_yes = max(0.1, min(0.9, simulated_poly_yes))

        # Notre estimation "juste" basée sur les indicateurs
        rsi_contrib  = (50 - ind.rsi_14) / 50 * 0.08  # oversold → +prob
        macd_contrib = np.sign(ind.macd_hist) * min(0.05, abs(ind.macd_hist / closes[-1]) * 5)
        ema_bull     = int(ind.ema9 > ind.ema21) + int(ind.ema21 > ind.ema50)
        ema_contrib  = (ema_bull - 1) * 0.04
        estimated_fair = 0.5 + rsi_contrib + macd_contrib + ema_contrib

        edge = estimated_fair - simulated_poly_yes

        # Injecter dans le force-graph
        aggregator.update(
            graph=graph,
            ind=ind,
            ind_signals=ind_sigs,
            tv=tv_signals,
            cq=cq_data,
            market=None,
            spot_price=closes[-1],
            poly_yes_price=simulated_poly_yes,
            estimated_true_prob=estimated_fair,
        )
        # Injecter l'edge manuellement
        graph.set_by_name("poly_edge", max(-1.0, min(1.0, edge / 0.05)))

        consensus = graph.compute()

        # Heure de la bougie
        ts = datetime.fromtimestamp(candle["time_ms"] / 1000, tz=timezone.utc)
        heure = ts.strftime("%H:%M")

        rsi_str  = f"{ind.rsi_14:.1f}"
        macd_str = f"{ind.macd_hist:+.0f}"
        field_str = f"{consensus.field:+.3f}"
        seuil_str = f"{'✓' if consensus.convergence >= FORCE_GRAPH_CONVERGENCE_THRESHOLD else '·'}{consensus.convergence:.2f}"

        # Signal
        signal_str = "—"
        pnl_str    = ""
        trade_color = RESET

        if (consensus.is_tradeable
                and abs(edge) >= MIN_EDGE_PCT
                and i < len(replay) - 1):

            direction = consensus.direction
            # Résolution = bougie suivante
            next_candle = candles[warmup + i + 2] if (warmup + i + 2) < len(candles) else candle
            btc_went_up = next_candle["close"] > candle["close"]

            # P&L simulé
            if direction == "BULL":
                entry = simulated_poly_yes
                # YES = 1.0 si BTC monte, 0.0 sinon
                resolved = 1.0 if btc_went_up else 0.0
            else:
                entry = 1.0 - simulated_poly_yes
                # NO = 1.0 si BTC baisse, 0.0 sinon
                resolved = 1.0 if not btc_went_up else 0.0

            size_usd = RISK_PER_TRADE_USD
            pnl = (resolved - entry) / entry * size_usd if entry > 0 else 0
            trades.append({
                "time": heure,
                "direction": direction,
                "entry": entry,
                "resolved": resolved,
                "pnl": pnl,
                "btc_move": (next_candle["close"] - candle["close"]) / candle["close"] * 100,
            })
            capital += pnl

            signal_str = direction[:4]
            pnl_str    = f"{pnl:+.2f}$"
            trade_color = GREEN if pnl > 0 else RED

        # Afficher chaque 4e bougie pour éviter le flood (25 lignes)
        if i % 4 == 0 or signal_str != "—":
            field_display = color(field_str, GREEN if consensus.field > 0 else (RED if consensus.field < -0.1 else YELLOW))
            signal_display = color(signal_str, trade_color)
            pnl_display    = color(pnl_str, trade_color)
            print(f"  {heure:<8} {closes[-1]:>10,.1f} {rsi_str:>6} {macd_str:>7} "
                  f"{field_display:>20} {seuil_str:>6} {signal_display:>16} {pnl_display:>17}")

    # ── Bilan ─────────────────────────────────────────────────────────────────
    print()
    print(color("═" * 65, CYAN))
    print(color("  BILAN SIMULATION — 8h30 de données réelles", BOLD))
    print(color("═" * 65, CYAN))

    n_trades = len(trades)
    if n_trades == 0:
        print(color("  Aucun trade généré (seuil de convergence non atteint)", YELLOW))
        print("  → Les conditions de marché n'ont pas permis de trouver d'edge.")
        print("    C'est normal : le bot ne trade PAS si les signaux sont absents.")
        return

    wins   = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    total_pnl = sum(t["pnl"] for t in trades)
    win_rate  = len(wins) / n_trades * 100

    print()
    print(f"  Trades simulés        : {color(str(n_trades), BOLD)}")
    print(f"  Victoires / Défaites  : {color(str(len(wins)), GREEN)} / {color(str(len(losses)), RED)}")
    print(f"  Taux de réussite      : {color(f'{win_rate:.1f}%', GREEN if win_rate >= 55 else RED)}")
    print(f"  P&L total simulé      : {color(f'{total_pnl:+.2f}$', GREEN if total_pnl > 0 else RED)}")
    print(f"  Capital final simulé  : {color(f'${capital:,.2f}', GREEN if capital > CAPITAL_USD else RED)}")
    print(f"  Rendement             : {color(f'{(capital/CAPITAL_USD-1)*100:+.2f}%', GREEN if capital > CAPITAL_USD else RED)}")

    if wins:
        avg_win = sum(t["pnl"] for t in wins) / len(wins)
        print(f"  Gain moyen/victoire   : {color(f'+{avg_win:.2f}$', GREEN)}")
    if losses:
        avg_loss = sum(t["pnl"] for t in losses) / len(losses)
        print(f"  Perte moyenne/défaite : {color(f'{avg_loss:.2f}$', RED)}")

    print()
    print(color("  Détail des trades :", BOLD))
    for t in trades:
        arrow = "↑" if t["direction"] == "BULL" else "↓"
        btc_result = "✓" if (t["direction"] == "BULL" and t["btc_move"] > 0) or \
                            (t["direction"] == "BEAR" and t["btc_move"] < 0) else "✗"
        pnl_c = GREEN if t["pnl"] > 0 else RED
        pnl_val = t["pnl"]
        pnl_colored = color(f"{pnl_val:+.2f}$", pnl_c)
        print(f"    {t['time']} {arrow}{t['direction']}  "
              f"entrée={t['entry']:.3f}  BTC{t['btc_move']:+.3f}%  "
              f"{btc_result}  {pnl_colored}")

    print()
    print(color("═" * 65, CYAN))
    print()

    # ── État du marché en ce moment ───────────────────────────────────────────
    print(color("  ÉTAT ACTUEL DU MARCHÉ", BOLD))
    print()

    # Calculer les indicateurs sur les toutes dernières bougies
    all_o = [c["open"]   for c in candles[-100:]]
    all_h = [c["high"]   for c in candles[-100:]]
    all_l = [c["low"]    for c in candles[-100:]]
    all_c = [c["close"]  for c in candles[-100:]]
    all_v = [c["volume"] for c in candles[-100:]]

    ind_now = engine.compute(all_o, all_h, all_l, all_c, all_v)
    sig_now = engine.normalize(ind_now)
    aggregator.update(graph, ind_now, sig_now, tv_signals, cq_data,
                      None, btc_now, poly_markets[0]["yes_price"] if poly_markets else 0.5,
                      0.5 + math.tanh(((all_c[-1]-all_c[-6])/all_c[-6]) / 0.004) * 0.12)
    consensus_now = graph.compute()

    print(f"  BTC/USDT              : {color(f'${btc_now:,.2f}', BOLD)}")
    print(f"  RSI 14                : {color(f'{ind_now.rsi_14:.1f}', GREEN if ind_now.rsi_14 < 40 else (RED if ind_now.rsi_14 > 60 else YELLOW))}")
    print(f"  MACD hist             : {color(f'{ind_now.macd_hist:+.1f}', GREEN if ind_now.macd_hist > 0 else RED)}")
    ema_align = "EMA9 > EMA21 > EMA50 ✓" if ind_now.ema9 > ind_now.ema21 > ind_now.ema50 else \
                "EMA9 < EMA21 < EMA50 ✓" if ind_now.ema9 < ind_now.ema21 < ind_now.ema50 else "Mixte"
    print(f"  Tendance EMA          : {ema_align}")
    print(f"  Force-graph field     : {color(f'{consensus_now.field:+.4f}', GREEN if consensus_now.field > 0 else RED)}")
    print(f"  Convergence           : {color(f'{consensus_now.convergence:.4f}', GREEN if consensus_now.is_tradeable else YELLOW)}")
    print(f"  Direction             : {color(consensus_now.direction, GREEN if consensus_now.direction == 'BULL' else (RED if consensus_now.direction == 'BEAR' else YELLOW))}")
    print(f"  Tradeable maintenant  : {color('OUI' if consensus_now.is_tradeable else 'NON', GREEN if consensus_now.is_tradeable else RED)}")

    if tv_signals.fresh:
        print(f"  TradingView 5M        : composite={tv_signals.tv_composite:+.3f}")

    if poly_markets:
        m = poly_markets[0]
        print(f"  Polymarket YES price  : {m['yes_price']:.4f} ({m['yes_price']*100:.1f}% prob hausse)")

    print()
    top = graph.top_contributors(consensus_now, 8)
    print(color("  Top contributeurs force-graph :", BOLD))
    for name, val in top:
        bar = "█" * int(abs(val) * 15)
        c_ = GREEN if val > 0 else RED
        print(f"    {name:<30} {color(f'{val:+.3f} {bar}', c_)}")

    print()
    print(color("═" * 65, CYAN))
    print()


if __name__ == "__main__":
    asyncio.run(run_simulation())
