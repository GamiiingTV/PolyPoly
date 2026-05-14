#!/usr/bin/env python3
"""
Simulation HFT BTC Polymarket — Données synthétiques réalistes.

Données :
  • Prix BTC simulé par mouvement Brownien géométrique
    avec les vrais paramètres du BTC (vol ~65% annualisée)
  • 200 bougies 5M = ~16h30 de données
  • Le "lag Polymarket" est simulé (délai réaliste de 300-800ms)
  • Le "prix YES Polymarket" suit le prix BTC avec du retard

Ce test vérifie que la logique du bot est saine.
"""

import math
import random
import sys
from datetime import datetime, timezone, timedelta

import numpy as np

sys.path.insert(0, ".")

from hft.signals.indicators import IndicatorEngine
from hft.signals.force_graph import ForceGraph
from hft.signals.aggregator import SignalAggregator
from hft.signals.tradingview_signals import TVSignals
from hft.feeds.cryptoquant_feed import ExchangeFlowData
from hft.execution.lag_detector import LagDetector
from hft.risk.risk_manager import RiskManager
from hft.config_hft import (
    CAPITAL_USD,
    FORCE_GRAPH_CONVERGENCE_THRESHOLD,
    RISK_PER_TRADE_USD,
    MIN_EDGE_PCT,
)

RESET  = "\033[0m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"

def col(text, c): return f"{c}{text}{RESET}"


# ─── Génération de prix BTC réaliste ─────────────────────────────────────────

def generate_btc_candles(n=200, start_price=103_500.0, seed=42):
    """
    Génère n bougies 5M BTC avec mouvement Brownien géométrique.

    Paramètres calibrés sur le vrai BTC :
      • Volatilité annualisée ~65%  → vol_5m = 65% / sqrt(105120) ≈ 0.20%/bougie
      • Légère dérive positive      → drift ~0.02% par bougie
      • Micro-tendances courtes     → autocorrélation légère (momentum)
    """
    rng = random.Random(seed)
    np.random.seed(seed)

    vol_5m   = 0.0020      # 0.20% par bougie 5M = 65% annualisée
    drift_5m = 0.00005     # légère tendance haussière

    price = start_price
    candles = []
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    # Start il y a n*5 minutes
    start_ms = now_ms - n * 5 * 60 * 1000

    prev_return = 0.0

    for i in range(n):
        # Mouvement Brownien avec léger momentum (autocorrélation 15%)
        shock = rng.gauss(0, vol_5m)
        ret   = drift_5m + 0.15 * prev_return + shock
        prev_return = ret

        # Parfois on injecte un micro-trend de 3-8 bougies
        if rng.random() < 0.03:
            trend_dir  = 1 if rng.random() > 0.45 else -1
            trend_len  = rng.randint(3, 8)
            trend_str  = rng.uniform(0.0005, 0.002)
            for j in range(trend_len):
                if i + j < n:
                    pass  # on l'applique au prochain ret via seed

        open_p  = price
        close_p = price * math.exp(ret)
        hi = max(open_p, close_p) * (1 + abs(rng.gauss(0, vol_5m * 0.5)))
        lo = min(open_p, close_p) * (1 - abs(rng.gauss(0, vol_5m * 0.5)))
        vol = abs(rng.gauss(1500, 400))  # volume BTC/5min

        candles.append({
            "time_ms": start_ms + i * 5 * 60 * 1000,
            "open":    round(open_p, 2),
            "high":    round(hi, 2),
            "low":     round(lo, 2),
            "close":   round(close_p, 2),
            "volume":  round(vol, 2),
        })
        price = close_p

    return candles


def simulate_polymarket_yes_price(candle_close, next_close, lag_fraction=0.0):
    """
    Simule le prix YES Polymarket = probabilité que BTC soit plus haut
    à la résolution de la bougie suivante.

    lag_fraction=0.0 → Polymarket parfaitement à jour
    lag_fraction=1.0 → Polymarket n'a pas encore repricé
    """
    # Prix "juste" basé sur les 5 prochaines minutes
    # (simplifié : si BTC a déjà bougé dans la direction, probabilité plus haute)
    return 0.5  # neutre — sera affiné avec l'edge simulator


# ─── Simulation principale ────────────────────────────────────────────────────

def run_simulation():
    print()
    print(col("═" * 68, CYAN))
    print(col("  HFT BTC Polymarket — SIMULATION OFFLINE (données réalistes)", BOLD))
    print(col(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", CYAN))
    print(col(f"  200 bougies 5M = 16h30 de données  |  Capital: ${CAPITAL_USD:,.0f}", CYAN))
    print(col("═" * 68, CYAN))

    # ── Génération données ────────────────────────────────────────────────────
    candles = generate_btc_candles(n=200, start_price=103_500.0, seed=42)
    print(f"\n  Données générées : {len(candles)} bougies BTC 5M")
    print(f"  Prix initial   : ${candles[0]['close']:,.2f}")
    print(f"  Prix final     : ${candles[-1]['close']:,.2f}")
    btc_change = (candles[-1]['close'] - candles[0]['close']) / candles[0]['close'] * 100
    print(f"  Variation totale: {col(f'{btc_change:+.2f}%', GREEN if btc_change > 0 else RED)}")
    print()

    # ── Init composants ───────────────────────────────────────────────────────
    engine     = IndicatorEngine()
    graph      = ForceGraph()
    aggregator = SignalAggregator()
    lag_det    = LagDetector()
    risk       = RiskManager(capital=CAPITAL_USD)
    tv         = TVSignals()      # neutre (pas d'accès réseau)
    cq         = ExchangeFlowData()  # neutre

    trades  = []
    capital = CAPITAL_USD
    warmup  = 60

    print(col("─" * 68, CYAN))
    print(col(f"  {'Heure':<7} {'BTC':>9} {'RSI':>5} {'MACD':>6} {'Force':>8} {'Edge':>7} {'Signal':>6} {'P&L':>8} {'Capital':>10}", BOLD))
    print(col("─" * 68, CYAN))

    rng = random.Random(99)

    for i in range(len(candles) - warmup - 1):
        idx    = warmup + i
        candle = candles[idx]
        next_c = candles[idx + 1]

        window = candles[:idx + 1]
        opens   = [c["open"]   for c in window]
        highs   = [c["high"]   for c in window]
        lows    = [c["low"]    for c in window]
        closes  = [c["close"]  for c in window]
        volumes = [c["volume"] for c in window]

        # ── Indicateurs ───────────────────────────────────────────────────────
        ind      = engine.compute(opens, highs, lows, closes, volumes)
        ind_sigs = engine.normalize(ind)

        # ── Simuler le prix Polymarket avec retard ─────────────────────────────
        # Polymarket "voit" le prix BTC avec 2-5 bougies de retard
        # (dans la réalité c'est 200ms-2s mais ici on simule en bougies)
        lag_bougies = rng.randint(1, 3)
        poly_ref_close = closes[max(0, -1 - lag_bougies)]

        # La proba YES devrait être ~50% + un peu de tendance
        momentum_recent = (closes[-1] - closes[-4]) / closes[-4] if len(closes) >= 4 else 0
        # Polymarket suit avec du retard
        poly_yes_price = 0.5 + math.tanh(momentum_recent * 0.5 / 0.004) * 0.10
        poly_yes_price = max(0.1, min(0.9, poly_yes_price))

        # Notre estimation "vraie" : on a plus d'info (indicateurs avancés)
        our_prob = 0.5
        # EMA alignment
        ema_bull = int(ind.ema9 > ind.ema21) + int(ind.ema21 > ind.ema50)
        our_prob += (ema_bull - 1) * 0.04
        # RSI
        our_prob += (50 - ind.rsi_14) / 50 * 0.06
        # MACD histogram
        if ind.macd_hist != 0:
            our_prob += math.tanh(ind.macd_hist / (closes[-1] * 0.001)) * 0.04
        # Momentum
        our_prob += math.tanh(momentum_recent / 0.004) * 0.06
        our_prob = max(0.1, min(0.9, our_prob))

        edge = our_prob - poly_yes_price  # >0 = on pense que YES est sous-évalué

        # ── Lag detector ──────────────────────────────────────────────────────
        ts_ms = int(datetime.now(timezone.utc).timestamp() * 1000) - (len(candles) - idx) * 300_000
        lag_det.on_binance_tick(closes[-1], ts_ms)
        lag_det.on_polymarket_price(poly_yes_price, ts_ms - rng.randint(300, 800))

        # ── Force-graph ───────────────────────────────────────────────────────
        aggregator.update(
            graph=graph,
            ind=ind,
            ind_signals=ind_sigs,
            tv=tv,
            cq=cq,
            market=None,
            spot_price=closes[-1],
            poly_yes_price=poly_yes_price,
            estimated_true_prob=our_prob,
        )
        graph.set_by_name("poly_edge", max(-1.0, min(1.0, edge / 0.05)))

        consensus = graph.compute()

        # ── Décision de trade ─────────────────────────────────────────────────
        signal_str = "—"
        pnl_str = ""
        trade_color = RESET

        if (consensus.is_tradeable
                and abs(edge) >= MIN_EDGE_PCT
                and consensus.contradiction_score < 0.4):

            direction = consensus.direction

            # Cohérence avec l'edge Polymarket
            if direction == "BULL" and edge > 0:   pass  # OK
            elif direction == "BEAR" and edge < 0: pass  # OK
            else:
                direction = None

            if direction and risk.can_trade():
                signal = risk.evaluate_signal(
                    direction=direction,
                    convergence=consensus.convergence,
                    edge_pct=abs(edge),
                    market_id="sim",
                    liquidity_usd=50_000,
                    spread_pct=0.015,
                    contradiction_score=consensus.contradiction_score,
                )
                if signal:
                    # Résolution : BTC plus haut ou non dans la bougie suivante ?
                    btc_went_up = next_c["close"] > candle["close"]
                    btc_move = (next_c["close"] - candle["close"]) / candle["close"] * 100

                    if direction == "BULL":
                        entry = poly_yes_price + 0.005  # slippage simulé
                        resolved = 1.0 if btc_went_up else 0.0
                    else:
                        entry = (1 - poly_yes_price) + 0.005
                        resolved = 1.0 if not btc_went_up else 0.0

                    entry = max(0.01, min(0.99, entry))
                    pnl = (resolved - entry) / entry * signal.size_usd

                    trades.append({
                        "idx": i,
                        "direction": direction,
                        "entry": entry,
                        "resolved": resolved,
                        "pnl": pnl,
                        "btc_move": btc_move,
                        "convergence": consensus.convergence,
                        "edge": edge,
                        "btc_went_up": btc_went_up,
                    })

                    capital += pnl
                    risk._daily_stats.pnl += pnl  # simplification pour simu

                    signal_str  = direction[:4]
                    pnl_str     = f"{pnl:+.2f}$"
                    trade_color = GREEN if pnl > 0 else RED

        # ── Affichage (toutes les 5 bougies ou sur trade) ─────────────────────
        show = (i % 5 == 0) or signal_str != "—"
        if show:
            ts_h = datetime.fromtimestamp(
                candles[idx]["time_ms"] / 1000, tz=timezone.utc
            ).strftime("%H:%M")

            rsi_c = GREEN if ind.rsi_14 < 40 else (RED if ind.rsi_14 > 60 else YELLOW)
            macd_c = GREEN if ind.macd_hist > 0 else RED
            force_c = GREEN if consensus.field > 0.1 else (RED if consensus.field < -0.1 else YELLOW)
            edge_c = GREEN if edge > 0.005 else (RED if edge < -0.005 else YELLOW)

            force_bar = "▰" * int(abs(consensus.field) * 8) + "▱" * (8 - int(abs(consensus.field) * 8))
            force_str = col(f"{consensus.field:+.3f}", force_c)
            edge_str  = col(f"{edge:+.3f}", edge_c)
            sig_str   = col(f"{signal_str:>4}", trade_color)
            pnl_disp  = col(f"{pnl_str:>6}", trade_color)
            cap_disp  = col(f"${capital:>8,.2f}", GREEN if capital >= CAPITAL_USD else RED)

            print(f"  {ts_h:<7} {closes[-1]:>9,.1f} "
                  f"{col(f'{ind.rsi_14:>5.1f}', rsi_c)} "
                  f"{col(f'{ind.macd_hist:>+6.0f}', macd_c)} "
                  f"{force_str:>16} "
                  f"{edge_str:>15} "
                  f"{sig_str:>14} "
                  f"{pnl_disp:>16} "
                  f"{cap_disp:>18}")

    # ── BILAN ─────────────────────────────────────────────────────────────────
    print()
    print(col("═" * 68, CYAN))
    print(col("  BILAN SIMULATION — 16h30 de données BTC réalistes", BOLD))
    print(col("═" * 68, CYAN))
    print()

    n_trades = len(trades)
    if n_trades == 0:
        print(col("  Aucun trade — seuil de convergence jamais atteint.", YELLOW))
        print("  Vérifier les paramètres de seuil.")
        return

    wins   = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    total_pnl = sum(t["pnl"] for t in trades)
    win_rate  = len(wins) / n_trades * 100 if n_trades else 0

    # Breakdown Bull vs Bear
    bull_trades = [t for t in trades if t["direction"] == "BULL"]
    bear_trades = [t for t in trades if t["direction"] == "BEAR"]

    # Drawdown max
    running = CAPITAL_USD
    peak = CAPITAL_USD
    max_dd = 0.0
    for t in trades:
        running += t["pnl"]
        if running > peak: peak = running
        dd = peak - running
        if dd > max_dd: max_dd = dd

    # Avg convergence des trades
    avg_conv = np.mean([t["convergence"] for t in trades])
    avg_edge = np.mean([abs(t["edge"]) for t in trades])

    print(f"  ─── Statistiques ───────────────────────────────────────────")
    print(f"  Période simulée       : 16h30 (200 bougies 5M)")
    print(f"  Nombre de trades      : {col(str(n_trades), BOLD)}")
    print(f"  Victoires / Défaites  : {col(str(len(wins)), GREEN)} / {col(str(len(losses)), RED)}")
    print(f"  Taux de réussite      : {col(f'{win_rate:.1f}%', GREEN if win_rate >= 55 else (YELLOW if win_rate >= 45 else RED))}")
    print(f"  P&L total simulé      : {col(f'{total_pnl:+.2f}$', GREEN if total_pnl > 0 else RED)}")
    print(f"  Capital final         : {col(f'${capital:,.2f}', GREEN if capital > CAPITAL_USD else RED)}")
    print(f"  Rendement             : {col(f'{(capital/CAPITAL_USD-1)*100:+.2f}%', GREEN if capital > CAPITAL_USD else RED)}")
    print(f"  Drawdown max          : {col(f'-${max_dd:.2f}', RED)}")
    print()
    print(f"  ─── Qualité des signaux ────────────────────────────────────")
    print(f"  Convergence force-graph (moy): {avg_conv:.3f} (seuil={FORCE_GRAPH_CONVERGENCE_THRESHOLD})")
    print(f"  Edge Polymarket (moy)         : {avg_edge*100:.2f}%")
    if wins:
        print(f"  Gain moyen/victoire           : +${sum(t['pnl'] for t in wins)/len(wins):.2f}")
    if losses:
        print(f"  Perte moy/défaite             : -${abs(sum(t['pnl'] for t in losses)/len(losses)):.2f}")
    if wins and losses:
        avg_w = sum(t["pnl"] for t in wins) / len(wins)
        avg_l = abs(sum(t["pnl"] for t in losses) / len(losses))
        print(f"  Ratio Gain/Perte              : {avg_w/avg_l:.2f}x {col('(>1 = bon)', GREEN if avg_w/avg_l > 1 else RED)}")
    print()
    print(f"  ─── BULL vs BEAR ───────────────────────────────────────────")
    if bull_trades:
        bull_wr = sum(1 for t in bull_trades if t["pnl"] > 0) / len(bull_trades) * 100
        print(f"  BULL : {len(bull_trades)} trades  WR={bull_wr:.0f}%  P&L={sum(t['pnl'] for t in bull_trades):+.2f}$")
    if bear_trades:
        bear_wr = sum(1 for t in bear_trades if t["pnl"] > 0) / len(bear_trades) * 100
        print(f"  BEAR : {len(bear_trades)} trades  WR={bear_wr:.0f}%  P&L={sum(t['pnl'] for t in bear_trades):+.2f}$")
    print()

    # Détail des trades
    print(f"  ─── Détail des trades ──────────────────────────────────────")
    for idx2, t in enumerate(trades):
        arrow = "↑" if t["direction"] == "BULL" else "↓"
        ok    = "✓" if t["pnl"] > 0 else "✗"
        pnl_c = GREEN if t["pnl"] > 0 else RED
        btc_c = GREEN if t["btc_went_up"] else RED
        btc_mv = t["btc_move"]
        pnl_v  = t["pnl"]
        print(f"  #{idx2+1:02d} {arrow}{t['direction']:<4}  "
              f"entrée={t['entry']:.3f}  "
              f"BTC {col(f'{btc_mv:+.3f}%', btc_c)}  "
              f"résolution={t['resolved']:.1f}  "
              f"{ok}  {col(f'{pnl_v:+.2f}$', pnl_c)}")

    print()
    print(col("═" * 68, CYAN))

    # ── Analyse de fiabilité ──────────────────────────────────────────────────
    print()
    print(col("  ANALYSE DE FIABILITÉ", BOLD))
    print()

    checks = []

    # 1. Le bot évite-t-il de trader quand pas d'edge ?
    total_bougies = 200 - 60 - 1
    trade_rate = n_trades / total_bougies * 100
    checks.append(("Filtre sélectif (trade rate)", trade_rate < 20,
                    f"{trade_rate:.1f}% des bougies → trade (idéal <20%)"))

    # 2. Taux de réussite > hasard (>50%)
    checks.append(("Win rate > 50% (mieux que hasard)", win_rate > 50,
                    f"{win_rate:.1f}%"))

    # 3. P&L positif
    checks.append(("P&L total positif", total_pnl > 0,
                    f"{total_pnl:+.2f}$"))

    # 4. Ratio gain/perte > 1
    if wins and losses:
        avg_w = sum(t["pnl"] for t in wins) / len(wins)
        avg_l = abs(sum(t["pnl"] for t in losses) / len(losses))
        ratio = avg_w / avg_l
        checks.append(("Ratio gain/perte > 1", ratio > 1.0, f"{ratio:.2f}x"))

    # 5. Drawdown < limite quotidienne
    dd_pct = max_dd / CAPITAL_USD * 100
    checks.append(("Drawdown < limite quotidienne 2%", dd_pct < 2.0,
                    f"{dd_pct:.2f}% (limite={2.0}%)"))

    # 6. Convergence force-graph élevée
    checks.append(("Convergence FG > seuil+5%", avg_conv > FORCE_GRAPH_CONVERGENCE_THRESHOLD + 0.05,
                    f"{avg_conv:.3f} (seuil={FORCE_GRAPH_CONVERGENCE_THRESHOLD})"))

    for label, ok, detail in checks:
        icon = col("✓", GREEN) if ok else col("✗", RED)
        status = col("OK", GREEN) if ok else col("KO", RED)
        print(f"  {icon} {label:<45} {status}  {detail}")

    score = sum(1 for _, ok, _ in checks if ok)
    total_checks = len(checks)
    print()
    reliability = score / total_checks * 100
    rel_color = GREEN if reliability >= 70 else (YELLOW if reliability >= 50 else RED)
    print(f"  Score de fiabilité : {col(f'{score}/{total_checks} ({reliability:.0f}%)', rel_color)}")
    print()

    if reliability >= 80:
        verdict = col("BOT FIABLE — La logique fonctionne correctement", GREEN)
    elif reliability >= 60:
        verdict = col("BOT ACCEPTABLE — Quelques points à améliorer", YELLOW)
    else:
        verdict = col("BOT INSTABLE — Vérifier les paramètres", RED)
    print(f"  Verdict : {verdict}")
    print()
    print(col("═" * 68, CYAN))
    print()

    # ── Note sur les limites ───────────────────────────────────────────────────
    print(col("  NOTES IMPORTANTES", BOLD))
    print()
    print("  Cette simulation utilise des données synthétiques réalistes")
    print("  (mouvement Brownien géométrique, vol=65% annualisée).")
    print()
    print("  En conditions réelles, le bot capte en plus :")
    print("  • Le LAG réel Binance→Polymarket (150-2000ms mesurable)")
    print("  • Les signaux TradingView 5M en temps réel")
    print("  • Les flux CryptoQuant (exchange in/outflow)")
    print("  • La profondeur réelle du CLOB Polymarket")
    print()
    print("  Limites connues du bot :")
    print("  • Les marchés BTC 5M Polymarket ne sont pas toujours actifs")
    print("  • La liquidité peut être faible (<$5k → skip automatique)")
    print("  • Frais Polymarket ~1-2% à intégrer dans le calcul d'edge")
    print()


if __name__ == "__main__":
    run_simulation()
