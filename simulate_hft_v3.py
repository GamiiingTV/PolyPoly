#!/usr/bin/env python3
"""
Simulation HFT v3 — Deux stratégies combinées.

Stratégie 1 : HFT Repricing (existant, gate assoupli)
  • Capture le lag Binance→Polymarket sur les gros mouvements
  • Gate LAG : 0.10% (vs 0.15% en v2), cooldown 1 bougie
  • Exit avant résolution — capture le repricing Polymarket

Stratégie 2 : Resolution Sniping (nouveau)
  • Entre sur un marché BTC 5M à 60-90 secondes de la résolution
  • Condition : BTC clairement directionnel (>0.15% depuis ouverture)
  • Entry : YES à ~0.87 si BULL, NO à ~0.87 si BEAR
  • Win : résout à 1.00 → +14.9% sur la mise
  • Loss : résout à 0.00 → -100% de la mise
  • WR modélisé : 85-90% (BTC clairement ahead 60s avant close)

Données : 288 bougies 5M = 24h BTC simulées
"""

import argparse
import math
import random
import sys
from datetime import datetime, timezone

import numpy as np

sys.path.insert(0, ".")

from hft.signals.indicators import IndicatorEngine
from hft.signals.force_graph import ForceGraph
from hft.signals.aggregator import SignalAggregator
from hft.signals.tradingview_signals import TVSignals
from hft.feeds.cryptoquant_feed import ExchangeFlowData
from hft.risk.risk_manager import RiskManager
from hft.config_hft import (
    CAPITAL_USD,
    FORCE_GRAPH_CONVERGENCE_THRESHOLD,
)

RESET = "\033[0m"
GREEN = "\033[92m"
RED   = "\033[91m"
CYAN  = "\033[96m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
YELL  = "\033[93m"

def col(t, c): return f"{c}{t}{RESET}"

# ── Paramètres v3 ─────────────────────────────────────────────────────────────

# Stratégie 1 : HFT repricing (assoupli vs v2)
LAG_TRIGGER_MOVE  = 0.0010   # 0.10% (était 0.15%)
LAG_COOLDOWN      = 1        # 1 bougie entre trades (était 3)
FEE_PCT           = 0.010
REPRICE_SENS      = 0.10
STOP_LOSS_FRAC    = 0.50
MIN_EDGE_SIM      = 0.025    # 2.5% (était 3%)

# Stratégie 2 : Resolution sniping
SNIPE_MIN_MOVE       = 0.0015  # BTC doit avoir bougé ≥0.15% depuis ouverture marché
SNIPE_ENTRY_PRICE    = 0.87    # Achète YES (ou NO) à 87 cents quand <90s à la résolution
SNIPE_WIN_PRICE      = 1.00    # Résolution favorable
SNIPE_LOSS_PRICE     = 0.00    # Résolution défavorable
SNIPE_FEE_PCT        = 0.010
SNIPE_COOLDOWN       = 6       # Bougies entre deux snipes (un marché toutes les 5min)
# Modèle WR du snipe : si BTC a bougé X% depuis ouverture avec 60s restantes
# P(win) = sigmoid((move_pct / 0.002) - 0.5) × 0.30 + 0.68
# move=0.15% → ~75%  |  move=0.25% → ~82%  |  move=0.40% → ~89%


# ── BTC candles ───────────────────────────────────────────────────────────────

def gen_candles(n=288, start=103_500.0, seed=42):
    rng = random.Random(seed)
    np.random.seed(seed)
    vol   = 0.0020
    drift = 0.00005
    price = start
    candles = []
    now_ms   = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_ms = now_ms - n * 5 * 60 * 1000
    prev_ret = 0.0
    for i in range(n):
        shock   = rng.gauss(0, vol)
        ret     = drift + 0.15 * prev_ret + shock
        prev_ret = ret
        op  = price
        cl  = price * math.exp(ret)
        hi  = max(op, cl) * (1 + abs(rng.gauss(0, vol * 0.5)))
        lo  = min(op, cl) * (1 - abs(rng.gauss(0, vol * 0.5)))
        vol_ = abs(rng.gauss(1500, 400))
        candles.append({"time_ms": start_ms + i*300_000,
                         "open": round(op,2), "high": round(hi,2),
                         "low": round(lo,2), "close": round(cl,2),
                         "volume": round(vol_,2)})
        price = cl
    return candles


# ── Simulation principale ─────────────────────────────────────────────────────

def run(capital: float, trade_size: float, snipe_size: float):
    print()
    print(col("═" * 74, CYAN))
    print(col("  HFT BTC Polymarket — SIMULATION v3", BOLD))
    print(col(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  "
              f"Capital ${capital:.0f}  |  HFT ${trade_size:.0f}/trade  |  Snipe ${snipe_size:.0f}/trade", CYAN))
    print(col("═" * 74, CYAN))

    candles = gen_candles(n=288, start=103_500.0, seed=42)
    btc_chg = (candles[-1]['close'] / candles[0]['close'] - 1) * 100
    print(f"\n  Données : {len(candles)} bougies 5M = 24h  "
          f"BTC ${candles[0]['close']:,.0f} → ${candles[-1]['close']:,.0f} "
          f"({col(f'{btc_chg:+.2f}%', GREEN)})")
    print()
    print(col(f"  {'Heure':<7} {'BTC':>9} {'FG':>7} {'Edge':>7} "
              f"{'Strat':>6} {'Entrée':>7} {'Sortie':>7} {'P&L':>8} {'Capital':>10}", BOLD))
    print(col("─" * 74, CYAN))

    # init
    engine  = IndicatorEngine()
    graph   = ForceGraph()
    agg     = SignalAggregator()
    risk    = RiskManager(capital=capital)
    tv      = TVSignals()
    cq      = ExchangeFlowData()
    rng     = random.Random(99)

    trades_hft   = []
    trades_snipe = []
    cap          = capital
    warmup       = 60

    last_hft_idx   = -99
    last_snipe_idx = -99

    # "ouverture" du marché courant : toutes les 5M une nouvelle résolution
    # On simule que chaque bougie = 1 marché BTC 5M (simplification)
    market_open_price: dict[int, float] = {}

    for i in range(len(candles) - warmup - 1):
        idx    = warmup + i
        candle = candles[idx]

        window  = candles[:idx + 1]
        opens   = [c["open"]   for c in window]
        highs   = [c["high"]   for c in window]
        lows    = [c["low"]    for c in window]
        closes  = [c["close"]  for c in window]
        volumes = [c["volume"] for c in window]

        ind      = engine.compute(opens, highs, lows, closes, volumes)
        ind_sigs = engine.normalize(ind)

        last_move = (closes[-1] - closes[-2]) / closes[-2] if len(closes) >= 2 else 0.0
        btc_up    = last_move > 0

        # Force-graph
        momentum = (closes[-1] - closes[-4]) / closes[-4] if len(closes) >= 4 else 0
        poly_yes = 0.5 + math.tanh(momentum * 0.5 / 0.004) * 0.10
        poly_yes = max(0.1, min(0.9, poly_yes))
        our_prob = 0.5
        ema_bull  = int(ind.ema9 > ind.ema21) + int(ind.ema21 > ind.ema50)
        our_prob += (ema_bull - 1) * 0.04
        our_prob += (50 - ind.rsi_14) / 50 * 0.06
        if ind.macd_hist:
            our_prob += math.tanh(ind.macd_hist / (closes[-1] * 0.001)) * 0.04
        our_prob += math.tanh(momentum / 0.004) * 0.06
        our_prob = max(0.1, min(0.9, our_prob))
        edge = our_prob - poly_yes

        agg.update(graph=graph, ind=ind, ind_signals=ind_sigs, tv=tv, cq=cq,
                   market=None, spot_price=closes[-1], poly_yes_price=poly_yes,
                   estimated_true_prob=our_prob)
        graph.set_by_name("poly_edge", max(-1.0, min(1.0, edge / 0.05)))
        consensus = graph.compute()

        ts = datetime.fromtimestamp(candles[idx]["time_ms"]/1000,
                                    tz=timezone.utc).strftime("%H:%M")

        strat_str = col("—", DIM)
        entry_str = ""
        exit_str  = ""
        pnl_str   = ""
        pnl_val   = 0.0

        # ── Stratégie 1 : HFT Repricing ───────────────────────────────────────
        lag_prob  = 1.0 / (1.0 + math.exp(-(abs(last_move) / 0.003 - 0.5)))
        lag_ok    = abs(last_move) >= LAG_TRIGGER_MOVE and rng.random() < lag_prob
        cool_ok   = (i - last_hft_idx) >= LAG_COOLDOWN

        if (lag_ok and cool_ok and consensus.is_tradeable
                and abs(edge) >= MIN_EDGE_SIM
                and consensus.contradiction_score < 0.4):

            direction = consensus.direction
            if direction == "BULL" and edge <= 0: direction = None
            if direction == "BEAR" and edge >= 0: direction = None
            if direction == "BULL" and not btc_up: direction = None
            if direction == "BEAR" and btc_up:    direction = None

            if direction:
                p_rep = 0.68 + ((consensus.convergence - FORCE_GRAPH_CONVERGENCE_THRESHOLD)
                                 / (1.0 - FORCE_GRAPH_CONVERGENCE_THRESHOLD)) * 0.20
                p_rep = max(0.60, min(0.90, p_rep))
                noise = max(0.1, rng.gauss(1.0, 0.25))
                r_amt = math.tanh(abs(last_move) / 0.003) * REPRICE_SENS * noise
                fee   = trade_size * FEE_PCT
                win   = rng.random() < p_rep

                if direction == "BULL":
                    entry = min(0.95, poly_yes + 0.005)
                    exit_ = min(0.95, entry + r_amt) if win else max(0.05, entry - r_amt * STOP_LOSS_FRAC)
                else:
                    entry = min(0.95, (1 - poly_yes) + 0.005)
                    exit_ = min(0.95, entry + r_amt) if win else max(0.05, entry - r_amt * STOP_LOSS_FRAC)

                pnl_val = (exit_ - entry) / entry * trade_size - fee
                cap    += pnl_val
                last_hft_idx = i

                trades_hft.append({"pnl": pnl_val, "win": win, "entry": entry, "exit": exit_,
                                    "dir": direction, "size": trade_size})
                risk._daily_stats.pnl += pnl_val

                strat_str = col(f"HFT {'↑' if direction=='BULL' else '↓'}", GREEN if win else RED)
                entry_str = f"{entry:.3f}"
                exit_str  = f"{exit_:.3f}"
                pnl_str   = col(f"{pnl_val:+.2f}$", GREEN if pnl_val > 0 else RED)

        # ── Stratégie 2 : Resolution Sniping ─────────────────────────────────
        # Simule : on est à 60s de la résolution d'un marché BTC 5M.
        # Le marché a ouvert il y a ~4 min, BTC a bougé de X% depuis.
        # Si move ≥ 0.15% et direction claire → snipe à 87 cents.
        snipe_cool = (i - last_snipe_idx) >= SNIPE_COOLDOWN

        # Mouvement depuis "ouverture marché" = dernières 4 bougies
        move_4c = (closes[-1] - closes[-5]) / closes[-5] if len(closes) >= 5 else 0.0

        if snipe_cool and abs(move_4c) >= SNIPE_MIN_MOVE and strat_str == col("—", DIM):
            # WR modélisé selon la clarté du mouvement
            wr_snipe = 1.0 / (1.0 + math.exp(-(abs(move_4c) / 0.002 - 0.5))) * 0.22 + 0.70
            wr_snipe = max(0.70, min(0.92, wr_snipe))

            snipe_dir = "BULL" if move_4c > 0 else "BEAR"
            fee_s     = snipe_size * SNIPE_FEE_PCT
            win_s     = rng.random() < wr_snipe

            entry_s   = SNIPE_ENTRY_PRICE
            exit_s    = SNIPE_WIN_PRICE if win_s else SNIPE_LOSS_PRICE
            pnl_s     = (exit_s - entry_s) / entry_s * snipe_size - fee_s

            cap += pnl_s
            last_snipe_idx = i
            trades_snipe.append({"pnl": pnl_s, "win": win_s, "entry": entry_s,
                                  "exit": exit_s, "dir": snipe_dir,
                                  "move4c": move_4c * 100, "wr": wr_snipe,
                                  "size": snipe_size})
            risk._daily_stats.pnl += pnl_s

            strat_str = col(f"SNP {'↑' if snipe_dir=='BULL' else '↓'}", GREEN if win_s else RED)
            entry_str = f"{entry_s:.3f}"
            exit_str  = f"{exit_s:.3f}"
            pnl_val   = pnl_s
            pnl_str   = col(f"{pnl_val:+.2f}$", GREEN if pnl_val > 0 else RED)

        # Affichage (1 ligne toutes les 8 bougies ou sur trade)
        if (i % 8 == 0) or (strat_str != col("—", DIM)):
            fg_c  = GREEN if consensus.field > 0.1 else (RED if consensus.field < -0.1 else YELL)
            e_c   = GREEN if edge > 0.005 else (RED if edge < -0.005 else YELL)
            c_str = col(f"${cap:>8,.2f}", GREEN if cap >= capital else RED)
            print(f"  {ts:<7} {closes[-1]:>9,.1f} "
                  f"{col(f'{consensus.field:+.3f}', fg_c):>15} "
                  f"{col(f'{edge:+.3f}', e_c):>15} "
                  f"{strat_str:>14} "
                  f"{entry_str:>7} {exit_str:>7} "
                  f"{pnl_str:>16} "
                  f"{c_str:>18}")

    # ── BILAN ──────────────────────────────────────────────────────────────────
    all_trades  = trades_hft + trades_snipe
    n_hft       = len(trades_hft)
    n_snipe     = len(trades_snipe)
    n_total     = len(all_trades)

    pnl_hft     = sum(t["pnl"] for t in trades_hft)
    pnl_snipe   = sum(t["pnl"] for t in trades_snipe)
    pnl_total   = pnl_hft + pnl_snipe

    wr_hft   = sum(1 for t in trades_hft   if t["win"]) / max(1, n_hft)   * 100
    wr_snipe = sum(1 for t in trades_snipe if t["win"]) / max(1, n_snipe) * 100

    wins_all  = [t for t in all_trades if t["pnl"] > 0]
    loses_all = [t for t in all_trades if t["pnl"] <= 0]
    avg_w = sum(t["pnl"] for t in wins_all)  / max(1, len(wins_all))
    avg_l = abs(sum(t["pnl"] for t in loses_all)) / max(1, len(loses_all))
    ratio = avg_w / avg_l if avg_l > 0 else 0

    peak = capital
    dd   = 0.0
    run_ = capital
    for t in sorted(all_trades, key=lambda x: id(x)):
        run_ += t["pnl"]
        if run_ > peak: peak = run_
        if peak - run_ > dd: dd = peak - run_

    print()
    print(col("═" * 74, CYAN))
    print(col("  BILAN v3 — 24h simulées", BOLD))
    print(col("═" * 74, CYAN))
    print()
    print(f"  ┌─ Stratégie HFT Repricing ──────────────────────────────────────")
    print(f"  │  Trades : {n_hft:>3}  |  WR : {col(f'{wr_hft:.0f}%', GREEN if wr_hft>=60 else YELL)}"
          f"  |  P&L : {col(f'{pnl_hft:+.2f}$', GREEN if pnl_hft>0 else RED)}")
    print(f"  ├─ Stratégie Resolution Sniping ─────────────────────────────────")
    print(f"  │  Trades : {n_snipe:>3}  |  WR : {col(f'{wr_snipe:.0f}%', GREEN if wr_snipe>=60 else YELL)}"
          f"  |  P&L : {col(f'{pnl_snipe:+.2f}$', GREEN if pnl_snipe>0 else RED)}")
    print(f"  └─ TOTAL ────────────────────────────────────────────────────────")
    print(f"     Trades  : {n_total}")
    wr_total = sum(1 for t in all_trades if t["pnl"] > 0) / max(1, n_total) * 100
    print(f"     Win rate: {col(f'{wr_total:.1f}%', GREEN)}")
    print(f"     Ratio G/P: {col(f'{ratio:.2f}x', GREEN if ratio>1.2 else YELL)}")
    print(f"     P&L net : {col(f'{pnl_total:+.2f}$', GREEN if pnl_total>0 else RED)}")
    print(f"     Capital : {col(f'${cap:,.2f}', GREEN if cap>capital else RED)}"
          f"  ({col(f'{(cap/capital-1)*100:+.1f}%', GREEN if cap>capital else RED)})")
    print(f"     Drawdown: {col(f'-${dd:.2f}', RED)}")
    print()

    # ── Projection 30 jours ────────────────────────────────────────────────────
    print(col("  PROJECTION COMPOUND — 30 jours", BOLD))
    print(col("  (base : P&L journalier = P&L 24h simulées ci-dessus)", DIM))
    print()
    print(f"  {'Jour':<6} {'Capital':>10} {'P&L jour':>10} {'Total gain':>12}")
    print(f"  {'─'*6} {'─'*10} {'─'*10} {'─'*12}")
    cap_proj     = capital
    daily_pnl    = pnl_total
    daily_trades = n_total

    for day in range(1, 31):
        # Compound : taille de trade grossit proportionnellement au capital
        scale        = cap_proj / capital
        day_pnl      = daily_pnl * scale
        cap_proj    += day_pnl
        total_gain   = cap_proj - capital
        marker = ""
        if day in (7, 14, 21, 30):
            marker = col(" ◄", CYAN)
        if day % 7 == 0 or day == 1 or day == 30:
            gain_c = GREEN if total_gain > 0 else RED
            print(f"  {f'J{day}':<6} {col(f'${cap_proj:>9,.2f}', gain_c)} "
                  f"{col(f'{day_pnl:>+9.2f}$', GREEN if day_pnl>0 else RED)} "
                  f"{col(f'{total_gain:>+11.2f}$', gain_c)}{marker}")

    print()
    roi_30 = (cap_proj / capital - 1) * 100
    roi_c  = GREEN if roi_30 > 0 else RED
    print(f"  ROI 30 jours   : {col(f'{roi_30:+.1f}%', roi_c)}")
    print(f"  Capital final  : {col(f'${cap_proj:,.2f}', roi_c)}")
    print()
    print(col("  Note : simulation sur données synthétiques seed fixe.", DIM))
    print(col("  Marchés réels = plus de liquidité, plus de marchés BTC actifs.", DIM))
    print(col("  Resolution sniping réel = ~4-8 opp/heure en période volatile.", DIM))
    print()
    print(col("═" * 74, CYAN))
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capital",    type=float, default=CAPITAL_USD)
    parser.add_argument("--trade-size", type=float, default=10.0)
    parser.add_argument("--snipe-size", type=float, default=10.0)
    args = parser.parse_args()
    run(capital=args.capital, trade_size=args.trade_size, snipe_size=args.snipe_size)
