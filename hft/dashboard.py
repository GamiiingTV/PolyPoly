"""
PolyPoly HFT — Terminal Dashboard v3
Orange-noir, deux stratégies, plein de kiff.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from rich import box
from rich.align import Align
from rich.layout import Layout
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

# ── Palette ───────────────────────────────────────────────────────────────────

O1    = "orange1"          # orange vif  (titres, accents)
O3    = "dark_orange"      # orange moyen (barres, labels)
WHT   = "bold bright_white"
GRN   = "bold bright_green"
RED   = "bold bright_red"
YEL   = "bold yellow"
CYN   = "bold cyan"
DIM   = "dim"
GREY  = "grey50"
PINK  = "bold magenta"

BLOCKS = " ▁▂▃▄▅▆▇█"

PIPELINE_STAGES = ["BINANCE", "INDIC.", "FORCE-G", "EV+GATE", "EXECUTE"]

LOGO = (
    "  ██████╗  ██████╗ ██╗  ██╗   ██╗██████╗  ██████╗ ██╗  ██╗   ██╗\n"
    "  ██╔══██╗██╔═══██╗██║  ╚██╗ ██╔╝██╔══██╗██╔═══██╗██║  ╚██╗ ██╔╝\n"
    "  ██████╔╝██║   ██║██║   ╚████╔╝ ██████╔╝██║   ██║██║   ╚████╔╝ \n"
    "  ██╔═══╝ ██║   ██║██║    ╚██╔╝  ██╔═══╝ ██║   ██║██║    ╚██╔╝  \n"
    "  ██║     ╚██████╔╝███████╗██║   ██║     ╚██████╔╝███████╗██║   \n"
    "  ╚═╝      ╚═════╝ ╚══════╝╚═╝   ╚═╝      ╚═════╝ ╚══════╝╚═╝   "
)


# ── BotState ──────────────────────────────────────────────────────────────────

@dataclass
class BotState:
    # Capital
    capital_start: float = 1000.0
    capital: float = 1000.0
    daily_pnl: float = 0.0

    # HFT repricing trades
    hft_trades: int = 0
    hft_wins: int = 0

    # Snipe trades
    snipe_trades: int = 0
    snipe_wins: int = 0

    # Totaux (pour compat rétro)
    total_trades: int = 0
    wins: int = 0
    losses: int = 0

    # BTC
    btc_price: float = 0.0
    btc_prev_price: float = 0.0
    btc_tick_count: int = 0

    # Force-graph
    fg_field: float = 0.0
    fg_convergence: float = 0.0
    fg_direction: str = "NEUTRAL"
    fg_contradiction: float = 0.0

    # Lag detector
    lag_ms: float = 500.0
    lag_windows_detected: int = 0
    lag_active: bool = False

    # Pipeline stage 0=idle 1-5=actif
    pipeline_stage: int = 0

    # Market Polymarket
    market_name: str = "Searching…"
    poly_yes_price: float = 0.5
    poly_spread_pct: float = 0.02
    poly_liquidity: float = 0.0
    snipe_seconds_left: float = 0.0   # secondes avant résolution marché

    # Dérivés Binance Perpetuals
    funding_rate: float = 0.0          # taux brut
    funding_signal: float = 0.0        # [-1, +1] (contrarian normalisé)
    oi_change_pct: float = 0.0         # variation OI sur 5 min (%)
    whale_buy_btc: float = 0.0         # whale BUY 30s
    whale_sell_btc: float = 0.0        # whale SELL 30s
    whale_pressure: float = 0.0        # [-1, +1]

    # Kelly sizing
    kelly_size: float = 10.0
    kelly_fraction: float = 0.0
    kelly_streak: int = 0
    kelly_burn_in: bool = True
    kelly_rr: float = 0.0

    # Historique
    recent_trades: list = field(default_factory=list)
    equity_history: list = field(default_factory=list)

    # Logs
    log_lines: object = field(default_factory=lambda: deque(maxlen=8))

    # Status
    is_live: bool = False
    is_halted: bool = False
    halt_reason: str = ""
    start_time: float = field(default_factory=time.time)
    lock: object = field(default_factory=threading.Lock)

    # ── Computed ─────────────────────────────────────────────────────────────

    @property
    def win_rate(self) -> float:
        return self.wins / self.total_trades if self.total_trades else 0.0

    @property
    def hft_wr(self) -> float:
        return self.hft_wins / self.hft_trades if self.hft_trades else 0.0

    @property
    def snipe_wr(self) -> float:
        return self.snipe_wins / self.snipe_trades if self.snipe_trades else 0.0

    @property
    def avg_rr(self) -> float:
        w = [t["pnl"] for t in self.recent_trades if t.get("pnl", 0) > 0]
        l = [abs(t["pnl"]) for t in self.recent_trades if t.get("pnl", 0) < 0]
        if not w or not l:
            return 0.0
        return (sum(w) / len(w)) / (sum(l) / len(l))

    @property
    def total_pnl(self) -> float:
        return self.capital - self.capital_start

    @property
    def total_pnl_pct(self) -> float:
        return (self.total_pnl / self.capital_start * 100) if self.capital_start else 0.0

    @property
    def uptime_str(self) -> str:
        e = int(time.time() - self.start_time)
        return f"{e // 3600}h {(e % 3600) // 60:02d}m {e % 60:02d}s"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _spark(values: list, width: int = 56) -> str:
    data = list(values)[-width:]
    if len(data) < 2:
        return "─" * width
    mn, mx = min(data), max(data)
    if mn == mx:
        return "─" * width
    return "".join(BLOCKS[min(8, int((v - mn) / (mx - mn) * 8.99))] for v in data)


def _pct_col(v: float) -> str:
    return GRN if v > 0 else (RED if v < 0 else DIM)


def _sgn(v: float, d: int = 2) -> str:
    return f"+{v:.{d}f}" if v >= 0 else f"{v:.{d}f}"


def _wr_col(wr: float) -> str:
    return GRN if wr >= 0.65 else (YEL if wr >= 0.50 else RED)


def _bar_orange(ratio: float, width: int = 18) -> Text:
    """Barre de progression orange pleine."""
    filled = min(width, int(ratio * width))
    empty  = width - filled
    t = Text()
    t.append("█" * filled, style=O1)
    t.append("░" * empty,  style=GREY)
    return t


def _force_bar(field_val: float, width: int = 22) -> Text:
    """Barre BULL/BEAR centrée."""
    filled = min(width, int(abs(field_val) * width))
    empty  = width - filled
    t = Text()
    if field_val >= 0:
        t.append("BULL ", style=GRN)
        t.append("█" * filled, style=GRN)
        t.append("░" * empty,  style=GREY)
        t.append(" BEAR", style=GREY)
    else:
        t.append("BULL ", style=GREY)
        t.append("░" * empty,  style=GREY)
        t.append("█" * filled, style=RED)
        t.append(" BEAR", style=RED)
    return t


# ── Dashboard ─────────────────────────────────────────────────────────────────

class HFTDashboard:
    def __init__(self, state: BotState) -> None:
        self.state = state
        self._tick = 0

    def render(self) -> Layout:
        self._tick += 1
        s = self.state

        root = Layout(name="root")
        root.split_column(
            Layout(name="header", size=5),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )
        root["body"].split_row(
            Layout(name="left",  ratio=38),
            Layout(name="right", ratio=62),
        )
        root["left"].split_column(
            Layout(name="capital",   size=9),
            Layout(name="strategies",size=7),
            Layout(name="kelly",     size=6),
            Layout(name="forceg",    size=6),
            Layout(name="pipeline",  size=5),
            Layout(name="logs"),
        )
        root["right"].split_column(
            Layout(name="derivs",  size=8),
            Layout(name="equity",  size=8),
            Layout(name="trades"),
        )

        root["header"].update(self._header(s))
        root["capital"].update(self._capital_panel(s))
        root["strategies"].update(self._strategies_panel(s))
        root["kelly"].update(self._kelly_panel(s))
        root["forceg"].update(self._fg_panel(s))
        root["pipeline"].update(self._pipeline_panel(s))
        root["logs"].update(self._log_panel(s))
        root["derivs"].update(self._derivs_panel(s))
        root["equity"].update(self._equity_panel(s))
        root["trades"].update(self._trades_panel(s))
        root["footer"].update(self._footer_panel(s))

        return root

    # ── Header ────────────────────────────────────────────────────────────────

    def _header(self, s: BotState) -> Panel:
        # Status badge animé
        pulse = ("◉", "○")[self._tick % 2]
        if s.is_halted:
            badge = Text(f" ■ HALTED  {s.halt_reason[:40]} ", style="bold black on red")
        elif s.is_live:
            badge = Text(f" {pulse} LIVE  uptime {s.uptime_str} ", style="bold black on bright_green")
        else:
            badge = Text(f" {pulse} PAPER  uptime {s.uptime_str} ", style="bold black on yellow")

        # BTC ticker
        delta     = s.btc_price - s.btc_prev_price
        arrow     = "▲" if delta >= 0 else "▼"
        btc_style = GRN if delta >= 0 else RED

        line1 = Text()
        line1.append("  BTC ", style=DIM)
        line1.append(f"${s.btc_price:>11,.2f} ", style=WHT)
        line1.append(f"{arrow} {abs(delta):,.2f}  ", style=btc_style)
        line1.append("│ ", style=GREY)
        line1.append("YES ", style=DIM)
        line1.append(f"{s.poly_yes_price:.3f}  ", style=CYN)
        line1.append("│ ", style=GREY)
        lag_c = O1 if s.lag_active else GREY
        line1.append("LAG ", style=DIM)
        line1.append(f"{s.lag_ms:.0f}ms  ", style=lag_c)
        line1.append("│ ", style=GREY)
        line1.append("WR ", style=DIM)
        line1.append(f"{s.win_rate*100:.1f}%  ", style=_wr_col(s.win_rate))
        line1.append("│ ", style=GREY)
        line1.append("TICKS ", style=DIM)
        line1.append(f"{s.btc_tick_count:,}", style=WHT)
        line1.append("  ")
        line1.append_text(badge)

        line2 = Text()
        line2.append("  MARKET  ", style=DIM)
        line2.append(s.market_name, style=f"bold {O1}")
        if s.snipe_seconds_left > 0:
            snipe_c = RED if s.snipe_seconds_left < 60 else YEL
            line2.append(f"  ⏱ {s.snipe_seconds_left:.0f}s", style=snipe_c)
        line2.append("  │  FG ", style=GREY)
        fg_c = GRN if s.fg_direction == "BULL" else (RED if s.fg_direction == "BEAR" else DIM)
        arrow2 = "▲" if s.fg_direction == "BULL" else ("▼" if s.fg_direction == "BEAR" else "─")
        line2.append(f"{arrow2} {s.fg_direction}  ", style=fg_c)
        line2.append(f"conv {s.fg_convergence*100:.1f}%  ", style=CYN)
        line2.append("│  SPREAD ", style=GREY)
        sp_c = GRN if s.poly_spread_pct < 0.025 else (YEL if s.poly_spread_pct < 0.04 else RED)
        line2.append(f"{s.poly_spread_pct*100:.2f}%  ", style=sp_c)
        line2.append("│  LIQ ", style=GREY)
        line2.append(f"${s.poly_liquidity:,.0f}", style=CYN)

        body = Text("\n").join([line1, line2])

        return Panel(
            body,
            title=Text("◈◈◈  P O L Y P O L Y   H F T   E N G I N E   v 3 . 0  ◈◈◈", style=f"bold {O1}"),
            style=O3,
            box=box.DOUBLE_EDGE,
            padding=(0, 1),
        )

    # ── Capital ───────────────────────────────────────────────────────────────

    def _capital_panel(self, s: BotState) -> Panel:
        pnl   = s.total_pnl
        pnl_c = GRN if pnl >= 0 else RED

        # Grande valeur capitale
        cap_text = Text()
        cap_text.append(f"  ${s.capital:>12,.2f}", style=f"bold {O1}")
        cap_text.append("\n")

        # P&L total
        cap_text.append("  Session total  ", style=DIM)
        cap_text.append(f"{_sgn(pnl):>10}", style=pnl_c)
        cap_text.append(f"  ({_sgn(s.total_pnl_pct, 1)}%)", style=pnl_c)
        cap_text.append("\n")

        # Daily P&L
        cap_text.append("  Journalier     ", style=DIM)
        cap_text.append(f"{_sgn(s.daily_pnl):>10}", style=_pct_col(s.daily_pnl))
        cap_text.append("\n")

        # Barre progression vers objectif (+20%)
        target = s.capital_start * 1.20
        ratio  = min(1.0, max(0.0, (s.capital - s.capital_start) / (target - s.capital_start))) if target != s.capital_start else 0.0
        cap_text.append("  Objectif +20%  ", style=DIM)
        cap_text.append_text(_bar_orange(ratio, width=20))
        cap_text.append(f"  {ratio*100:.0f}%\n", style=O1)

        # Trades résumé
        cap_text.append(f"  {s.total_trades} trades  ", style=DIM)
        cap_text.append(f"✓{s.wins}", style=GRN)
        cap_text.append("  ", style=DIM)
        cap_text.append(f"✗{s.losses}", style=RED)
        cap_text.append(f"  R:R {s.avg_rr:.2f}", style=CYN)

        return Panel(
            cap_text,
            title=Text(f"◈ CAPITAL", style=f"bold {O1}"),
            box=box.DOUBLE_EDGE,
            style="on grey7",
            padding=(0, 1),
        )

    # ── Stratégies ────────────────────────────────────────────────────────────

    def _strategies_panel(self, s: BotState) -> Panel:
        t = Text()

        # Entêtes
        t.append(f"  {'':20}", style=DIM)
        t.append(f"{'HFT':>10}", style=f"bold {O1}")
        t.append(f"{'SNIPE':>12}", style=f"bold {CYN}")
        t.append("\n")

        # Séparateur
        t.append("  " + "─" * 40 + "\n", style=GREY)

        # Trades
        t.append("  Trades         ", style=DIM)
        t.append(f"{s.hft_trades:>10}", style=WHT)
        t.append(f"{s.snipe_trades:>12}\n", style=WHT)

        # Win rate
        t.append("  Win rate       ", style=DIM)
        t.append(f"{s.hft_wr*100:>9.1f}%", style=_wr_col(s.hft_wr))
        t.append(f"{s.snipe_wr*100:>11.1f}%\n", style=_wr_col(s.snipe_wr))

        # P&L calculé depuis recent_trades
        hft_pnl   = sum(t2["pnl"] for t2 in s.recent_trades if t2.get("strat") == "HFT")
        snipe_pnl = sum(t2["pnl"] for t2 in s.recent_trades if t2.get("strat") == "SNP")
        t.append("  P&L session    ", style=DIM)
        t.append(f"{_sgn(hft_pnl):>10}", style=_pct_col(hft_pnl))
        t.append(f"{_sgn(snipe_pnl):>12}\n", style=_pct_col(snipe_pnl))

        return Panel(
            t,
            title=Text("◈ STRATÉGIES  HFT + SNIPE", style=f"bold {O1}"),
            box=box.DOUBLE_EDGE,
            style="on grey7",
            padding=(0, 0),
        )

    # ── Kelly Sizer ───────────────────────────────────────────────────────────

    def _kelly_panel(self, s: BotState) -> Panel:
        t = Text()
        size_c = O1
        # Streak indicator
        if s.kelly_streak >= 3:
            streak_str = f"🔥 WIN×{s.kelly_streak}"
            streak_c   = GRN
        elif s.kelly_streak <= -3:
            streak_str = f"❄ LOSS×{abs(s.kelly_streak)}"
            streak_c   = RED
        else:
            streak_str = f"{s.kelly_streak:+d}"
            streak_c   = DIM

        t.append("  Prochaine mise  ", style=DIM)
        t.append(f"${s.kelly_size:>6.2f}", style=f"bold {size_c}")
        t.append("\n")

        if s.kelly_burn_in:
            t.append("  ", style=DIM)
            t.append("BURN-IN ", style=YEL)
            t.append("— mise fixe jusqu'à 20 trades", style=DIM)
            t.append("\n")
        else:
            t.append("  Kelly fraction  ", style=DIM)
            t.append(f"{s.kelly_fraction*100:>5.2f}%  ", style=CYN)
            t.append("R:R ", style=DIM)
            t.append(f"{s.kelly_rr:.2f}", style=CYN)
            t.append("\n")

        t.append("  Streak  ", style=DIM)
        t.append(streak_str, style=f"bold {streak_c}")

        return Panel(
            t,
            title=Text("◈ KELLY ADAPTIVE", style=f"bold {O1}"),
            box=box.DOUBLE_EDGE,
            style="on grey7",
            padding=(0, 1),
        )

    # ── Dérivés Binance Perpetuals ────────────────────────────────────────────

    def _derivs_panel(self, s: BotState) -> Panel:
        t = Text()

        # Funding rate avec interprétation
        funding_pct = s.funding_rate * 100
        if s.funding_signal > 0.3:
            funding_label = "BULL contrarian"
            f_c = GRN
        elif s.funding_signal < -0.3:
            funding_label = "BEAR (longs over)"
            f_c = RED
        else:
            funding_label = "neutre"
            f_c = DIM

        t.append("  FUNDING  ", style=DIM)
        t.append(f"{funding_pct:+.4f}%  ", style=WHT)
        t.append(f"→ {funding_label}", style=f_c)
        t.append("\n")

        # Open Interest
        oi_c = GRN if s.oi_change_pct > 0.5 else (RED if s.oi_change_pct < -0.5 else DIM)
        t.append("  OPEN INT. ", style=DIM)
        t.append(f"Δ5m {_sgn(s.oi_change_pct, 2)}%  ", style=oi_c)
        if abs(s.oi_change_pct) > 0.5:
            interpret = "build-up" if s.oi_change_pct > 0 else "unwind"
            t.append(f"({interpret})", style=DIM)
        t.append("\n")

        # Whales
        total_w = s.whale_buy_btc + s.whale_sell_btc
        t.append("  WHALES 30s  ", style=DIM)
        t.append(f"BUY ", style=DIM)
        t.append(f"{s.whale_buy_btc:.2f}", style=GRN)
        t.append(" / ", style=DIM)
        t.append(f"SELL ", style=DIM)
        t.append(f"{s.whale_sell_btc:.2f}", style=RED)
        t.append("  ($", style=DIM)
        t.append(f"{total_w * s.btc_price / 1000:.0f}k", style=CYN)
        t.append(")\n")

        # Whale pressure bar
        t.append("  Pressure   ", style=DIM)
        if s.whale_pressure >= 0:
            t.append_text(_force_bar(s.whale_pressure, width=18))
        else:
            t.append_text(_force_bar(s.whale_pressure, width=18))
        t.append(f"  {_sgn(s.whale_pressure, 2)}", style=O1)

        return Panel(
            t,
            title=Text("◈ DÉRIVÉS BTC PERP  ·  funding · OI · whales", style=f"bold {O1}"),
            box=box.DOUBLE_EDGE,
            style="on grey7",
            padding=(0, 1),
        )

    # ── Force-graph ───────────────────────────────────────────────────────────

    def _fg_panel(self, s: BotState) -> Panel:
        t = Text()
        t.append("  ")
        t.append_text(_force_bar(max(-1.0, min(1.0, s.fg_field))))
        t.append("\n")
        t.append("  Field ", style=DIM)
        t.append(f"{_sgn(s.fg_field, 3):<8}", style=O1)
        t.append("Conv ", style=DIM)
        t.append(f"{s.fg_convergence*100:.1f}%  ", style=CYN)
        t.append("Contra ", style=DIM)
        t.append(f"{s.fg_contradiction*100:.1f}%", style=YEL)
        t.append("\n")
        lag_c = O1 if s.lag_active else GREY
        active = "◉ ACTIVE" if s.lag_active else "○ idle"
        t.append("  LAG WINDOW  ", style=DIM)
        t.append(f"{active}  ", style=lag_c)
        t.append(f"×{s.lag_windows_detected} detected", style=DIM)

        return Panel(
            t,
            title=Text("◈ FORCE-GRAPH", style=f"bold {O1}"),
            box=box.DOUBLE_EDGE,
            style="on grey7",
            padding=(0, 1),
        )

    # ── Pipeline ──────────────────────────────────────────────────────────────

    def _pipeline_panel(self, s: BotState) -> Panel:
        stage = s.pipeline_stage
        t = Text()
        t.append("  ")
        for i, name in enumerate(PIPELINE_STAGES, 1):
            if stage == 0:
                sym, sty = "○", DIM
            elif i < stage:
                sym, sty = "●", GRN
            elif i == stage:
                sym, sty = "◉", f"bold {O1}"
            else:
                sym, sty = "○", DIM
            t.append(f"{sym}{name} ", style=sty)
            if i < len(PIPELINE_STAGES):
                t.append("→", style=GRN if (stage > 0 and i < stage) else GREY)

        t.append("\n  ", style=DIM)
        if stage == 0:
            t.append("IDLE — en attente de signal", style=DIM)
        else:
            t.append(PIPELINE_STAGES[stage - 1], style=f"bold {O1}")
            t.append(" en cours…", style=DIM)

        return Panel(
            t,
            title=Text("◈ PIPELINE", style=f"bold {O1}"),
            box=box.DOUBLE_EDGE,
            style="on grey7",
            padding=(0, 1),
        )

    # ── Logs ──────────────────────────────────────────────────────────────────

    def _log_panel(self, s: BotState) -> Panel:
        level_styles = {
            "INFO":  CYN,
            "WARN":  YEL,
            "ERROR": RED,
            "TRADE": f"bold {O1}",
            "SNIPE": f"bold {CYN}",
            "HALT":  RED,
            "DEBUG": DIM,
        }
        t = Text()
        lines = list(s.log_lines)
        if not lines:
            t.append("  en attente d'événements…", style=DIM)
        for level, msg in lines:
            sty = level_styles.get(level.upper(), DIM)
            t.append(f" [{level[:5]:5s}] ", style=sty)
            t.append(f"{msg}\n", style="white")

        return Panel(
            t,
            title=Text("◈ EVENT LOG", style=f"bold {O1}"),
            box=box.DOUBLE_EDGE,
            style="on grey7",
            padding=(0, 0),
        )

    # ── Equity curve ──────────────────────────────────────────────────────────

    def _equity_panel(self, s: BotState) -> Panel:
        hist = s.equity_history
        spark = _spark(hist, width=62)

        start = hist[0] if hist else s.capital_start
        end   = hist[-1] if hist else s.capital
        delta = end - start
        dc    = GRN if delta >= 0 else RED

        # Drawdown
        if len(hist) >= 2:
            pk = max(hist)
            idx_pk = hist.index(pk)
            tr = min(hist[idx_pk:]) if idx_pk < len(hist) - 1 else end
            dd = (tr - pk) / pk * 100 if pk else 0.0
        else:
            dd = 0.0

        t = Text()
        t.append("  ")
        t.append(spark, style=GRN if delta >= 0 else RED)
        t.append("\n")
        t.append(f"  Départ ${start:,.2f}  ", style=DIM)
        t.append(f"Actuel ${end:,.2f}  ", style=WHT)
        t.append(f"Δ {_sgn(delta)}$  ({_sgn(delta/start*100 if start else 0,1)}%)", style=dc)
        t.append("\n")
        t.append(f"  Max drawdown : ", style=DIM)
        t.append(f"{dd:.2f}%  ", style=RED if dd < -1 else GREY)
        t.append(f"({len(hist)} points)", style=DIM)

        return Panel(
            t,
            title=Text("◈ COURBE D'ÉQUITÉ", style=f"bold {O1}"),
            box=box.DOUBLE_EDGE,
            style="on grey7",
            padding=(0, 1),
        )

    # ── Trades table ──────────────────────────────────────────────────────────

    def _trades_panel(self, s: BotState) -> Panel:
        tbl = Table(
            box=box.SIMPLE_HEAD,
            style="on grey7",
            header_style=f"bold {O1}",
            show_edge=False,
            expand=True,
            padding=(0, 1),
        )
        tbl.add_column("#",      justify="right",  width=4,  style=DIM)
        tbl.add_column("STRAT",  justify="center", width=6)
        tbl.add_column("DIR",    justify="center", width=6)
        tbl.add_column("ENTRÉE", justify="right",  width=8)
        tbl.add_column("SORTIE", justify="right",  width=8)
        tbl.add_column("BTC Δ",  justify="right",  width=8)
        tbl.add_column("MISE",   justify="right",  width=7)
        tbl.add_column("P&L",    justify="right",  width=10)
        tbl.add_column("",       justify="center", width=3)

        trades = list(s.recent_trades)[-10:]
        total  = len(s.recent_trades)

        for i, tr in enumerate(reversed(trades), 1):
            idx    = total - i + 1
            strat  = tr.get("strat", "HFT")
            direct = tr.get("direction", "?")
            entry  = tr.get("entry",  0.0)
            exit_  = tr.get("exit",   0.0)
            pnl    = tr.get("pnl",    0.0)
            btcmv  = tr.get("btc_move", 0.0)
            size   = tr.get("size_usd", 0.0)

            strat_col = O1 if strat == "HFT" else CYN
            dir_col   = GRN if direct in ("UP", "BULL") else RED
            pnl_col   = GRN if pnl >= 0 else RED
            result    = "✓" if pnl >= 0 else "✗"
            result_c  = "bright_green" if pnl >= 0 else "bright_red"
            row_s     = "on grey11" if i % 2 == 0 else ""
            arrow     = "▲" if direct in ("UP", "BULL") else "▼"

            tbl.add_row(
                str(idx),
                Text(strat,              style=f"bold {strat_col}"),
                Text(f"{arrow}{direct}", style=dir_col),
                f"{entry:.3f}",
                f"{exit_:.3f}",
                Text(f"{_sgn(btcmv,1)}%", style=GRN if btcmv >= 0 else RED),
                f"${size:.0f}",
                Text(f"{_sgn(pnl)}$",   style=pnl_col),
                Text(result,            style=result_c),
                style=row_s,
            )

        if not trades:
            tbl.add_row("─", "─", "─", "─", "─", "─", "─", "─", "─", style=DIM)

        return Panel(
            tbl,
            title=Text(f"◈ TRADES RÉCENTS  ({total} total)", style=f"bold {O1}"),
            box=box.DOUBLE_EDGE,
            style="on grey7",
            padding=(0, 0),
        )

    # ── Footer ────────────────────────────────────────────────────────────────

    def _footer_panel(self, s: BotState) -> Panel:
        ev = (s.win_rate * s.avg_rr) - (1 - s.win_rate) if s.avg_rr > 0 else 0.0

        t = Text()
        t.append("  EV ", style=DIM)
        t.append(f"{_sgn(ev, 3)}  ", style=_pct_col(ev))
        t.append("│ ", style=GREY)
        t.append("CONV GATE ", style=DIM)
        gate_ok = s.fg_convergence >= 0.65
        t.append(f"{'OPEN' if gate_ok else 'CLOSED'} ({s.fg_convergence*100:.1f}%)  ",
                 style=GRN if gate_ok else GREY)
        t.append("│ ", style=GREY)
        t.append("SPREAD ", style=DIM)
        sp_c = GRN if s.poly_spread_pct < 0.025 else (YEL if s.poly_spread_pct < 0.04 else RED)
        t.append(f"{s.poly_spread_pct*100:.2f}%  ", style=sp_c)
        t.append("│ ", style=GREY)
        t.append("LIQ ", style=DIM)
        t.append(f"${s.poly_liquidity:,.0f}  ", style=CYN)
        t.append("│ ", style=GREY)
        t.append("LAG WINDOWS ", style=DIM)
        t.append(f"×{s.lag_windows_detected}  ", style=O1)
        t.append("│ ", style=GREY)
        t.append("SNIPE ⏱ ", style=DIM)
        snipe_c = RED if s.snipe_seconds_left < 60 and s.snipe_seconds_left > 0 else GREY
        t.append(f"{s.snipe_seconds_left:.0f}s", style=snipe_c)

        return Panel(
            t,
            style=O3,
            box=box.DOUBLE_EDGE,
            padding=(0, 1),
        )
