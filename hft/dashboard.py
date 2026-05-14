"""
HFT Dashboard — MIROFISH POLYBENCH ENGINE
Rich-library terminal dashboard for the BTC UP/DOWN binary market bot.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ORANGE = "dark_orange"
BRIGHT_WHITE = "bold bright_white"
DIM = "dim"
GREEN = "bold bright_green"
RED = "bold bright_red"
YELLOW = "bold yellow"
CYAN = "bold cyan"

PIPELINE_STAGES = ["BINANCE", "INDICATORS", "FORCE-GRAPH", "EV+ GATE", "EXECUTE"]

BLOCKS = " ▁▂▃▄▅▆▇█"

# ---------------------------------------------------------------------------
# BotState dataclass
# ---------------------------------------------------------------------------


@dataclass
class BotState:
    # Capital
    capital_start: float = 1000.0
    capital: float = 1000.0
    daily_pnl: float = 0.0

    # Trades
    total_trades: int = 0
    wins: int = 0
    losses: int = 0

    # BTC
    btc_price: float = 0.0
    btc_prev_price: float = 0.0  # 1 second ago
    btc_tick_count: int = 0

    # Force-graph
    fg_field: float = 0.0         # [-1, +1]
    fg_convergence: float = 0.0   # [0, 1]
    fg_direction: str = "NEUTRAL"
    fg_contradiction: float = 0.0

    # Lag detector
    lag_ms: float = 500.0
    lag_windows_detected: int = 0
    lag_active: bool = False

    # Pipeline stage (0=idle, 1=tick, 2=ind, 3=fg, 4=gate, 5=exec)
    pipeline_stage: int = 0

    # Market
    market_name: str = "N/A"
    poly_yes_price: float = 0.5
    poly_spread_pct: float = 0.02
    poly_liquidity: float = 0.0

    # History
    recent_trades: list = field(default_factory=list)
    # dicts: {direction, entry, exit, pnl, repriced, btc_move}
    equity_history: list = field(default_factory=list)
    # list of float capital values

    # Logs
    log_lines: object = field(default_factory=lambda: deque(maxlen=6))
    # (level, message) tuples

    # Status
    is_live: bool = False
    is_halted: bool = False
    halt_reason: str = ""
    start_time: float = field(default_factory=time.time)
    lock: object = field(default_factory=threading.Lock)

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.wins / self.total_trades

    @property
    def avg_rr(self) -> float:
        wins = [t["pnl"] for t in self.recent_trades if t.get("pnl", 0) > 0]
        losses = [abs(t["pnl"]) for t in self.recent_trades if t.get("pnl", 0) < 0]
        if not wins or not losses:
            return 0.0
        return (sum(wins) / len(wins)) / (sum(losses) / len(losses))

    @property
    def total_pnl(self) -> float:
        return self.capital - self.capital_start

    @property
    def total_pnl_pct(self) -> float:
        if self.capital_start == 0:
            return 0.0
        return (self.total_pnl / self.capital_start) * 100.0

    @property
    def uptime_str(self) -> str:
        elapsed = int(time.time() - self.start_time)
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        return f"{hours}h {minutes:02d}m"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sparkline(values: list, width: int = 50) -> str:
    if len(values) < 2:
        return "─" * width
    data = list(values)[-width:]
    mn, mx = min(data), max(data)
    if mn == mx:
        return "─" * width
    return "".join(
        BLOCKS[min(8, int((v - mn) / (mx - mn) * 8.99))] for v in data
    )


def _pct_color(value: float) -> str:
    if value > 0:
        return GREEN
    if value < 0:
        return RED
    return DIM


def _signed(value: float, decimals: int = 2) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{decimals}f}"


def _force_bar(field_val: float, width: int = 20) -> str:
    """Return a unicode block bar centred at zero."""
    # field_val in [-1, 1]; positive = BULL, negative = BEAR
    filled = int(abs(field_val) * width)
    filled = min(filled, width)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    return bar


# ---------------------------------------------------------------------------
# HFTDashboard
# ---------------------------------------------------------------------------


class HFTDashboard:
    """
    Rich terminal dashboard for the MIROFISH POLYBENCH HFT engine.
    Call render() inside a rich.live.Live context.
    """

    def __init__(self, state: BotState) -> None:
        self.state = state
        self._tick = 0  # internal frame counter for animations

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render(self) -> Layout:
        self._tick += 1
        s = self.state

        root = Layout(name="root")
        root.split_column(
            Layout(name="header", size=4),
            Layout(name="body"),
            Layout(name="footer", size=4),
        )

        root["body"].split_row(
            Layout(name="left", ratio=35),
            Layout(name="right", ratio=65),
        )

        root["left"].split_column(
            Layout(name="pnl", size=10),
            Layout(name="forcegraph", size=8),
            Layout(name="pipeline", size=7),
            Layout(name="logs"),
        )

        root["right"].split_column(
            Layout(name="equity", size=9),
            Layout(name="trades"),
        )

        root["header"].update(self._header_panel(s))
        root["pnl"].update(self._pnl_panel(s))
        root["forcegraph"].update(self._force_graph_panel(s))
        root["pipeline"].update(self._pipeline_panel(s))
        root["logs"].update(self._log_panel(s))
        root["equity"].update(self._equity_panel(s))
        root["trades"].update(self._trades_panel(s))
        root["footer"].update(self._footer_panel(s))

        return root

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _header_panel(self, s: BotState) -> Panel:
        # Status badge
        if s.is_halted:
            status_text = Text(" ■ HALTED ", style="bold black on red")
            status_detail = Text(f"  {s.halt_reason}", style=RED)
        elif s.is_live:
            pulse = "◉" if self._tick % 2 == 0 else "○"
            status_text = Text(f" {pulse} LIVE ", style="bold black on bright_green")
            status_detail = Text(f"  uptime {s.uptime_str}", style=GREEN)
        else:
            status_text = Text(" ◌ PAPER ", style="bold black on yellow")
            status_detail = Text(f"  uptime {s.uptime_str}", style=YELLOW)

        # BTC price and delta
        btc_delta = s.btc_price - s.btc_prev_price
        btc_arrow = "▲" if btc_delta >= 0 else "▼"
        btc_color = GREEN if btc_delta >= 0 else RED
        btc_text = Text()
        btc_text.append("BTC  ", style=DIM)
        btc_text.append(f"${s.btc_price:>10,.2f}  ", style="bold white")
        btc_text.append(f"{btc_arrow} {abs(btc_delta):.2f}", style=btc_color)

        # Ticker tape line
        lag_color = RED if s.lag_active else GREEN
        ticker = Text()
        ticker.append("▌", style=ORANGE)
        ticker.append(" POLYBENCH ", style=f"bold {ORANGE}")
        ticker.append("▐  ", style=ORANGE)
        ticker.append(btc_text)
        ticker.append("   │   ", style=DIM)
        ticker.append("YES ", style=DIM)
        ticker.append(f"{s.poly_yes_price:.3f}", style=CYAN)
        ticker.append("   │   ", style=DIM)
        ticker.append("LAG ", style=DIM)
        ticker.append(f"{s.lag_ms:.0f}ms", style=lag_color)
        ticker.append("   │   ", style=DIM)
        ticker.append("WR ", style=DIM)
        ticker.append(f"{s.win_rate*100:.1f}%", style=_pct_color(s.win_rate - 0.5))
        ticker.append("   │   ", style=DIM)
        ticker.append("TICKS ", style=DIM)
        ticker.append(f"{s.btc_tick_count:,}", style="bold white")

        # Second line: status
        line2 = Text()
        line2.append(status_text)
        line2.append(status_detail)
        line2.append("   ", style=DIM)
        line2.append("MARKET  ", style=DIM)
        line2.append(s.market_name, style=f"bold {ORANGE}")
        line2.append("   FG:", style=DIM)
        fg_color = GREEN if s.fg_direction == "BULL" else (RED if s.fg_direction == "BEAR" else DIM)
        line2.append(f" {s.fg_direction}", style=fg_color)

        body = Text("\n").join([ticker, line2])

        return Panel(
            body,
            style=f"bold {ORANGE}",
            box=box.HEAVY_EDGE,
            padding=(0, 1),
        )

    # ------------------------------------------------------------------
    # PNL panel
    # ------------------------------------------------------------------

    def _pnl_panel(self, s: BotState) -> Panel:
        pnl = s.total_pnl
        pnl_pct = s.total_pnl_pct
        color = _pct_color(pnl)

        t = Text()
        t.append("  CAPITAL  ", style=DIM)
        t.append(f"${s.capital:,.2f}\n", style=BRIGHT_WHITE)
        t.append("  ALL-TIME  ", style=DIM)

        sign = "+" if pnl >= 0 else ""
        t.append(f"  {sign}${pnl:,.2f}  ", style=f"bold {'bright_green' if pnl >= 0 else 'bright_red'} on grey7")
        t.append(f"  ({sign}{pnl_pct:.2f}%)\n", style=color)

        t.append("  DAILY P&L  ", style=DIM)
        daily_color = _pct_color(s.daily_pnl)
        t.append(f"{_signed(s.daily_pnl)}  ", style=daily_color)
        t.append("  TRADES ", style=DIM)
        t.append(f"{s.total_trades}  ", style=BRIGHT_WHITE)
        t.append("W ", style=GREEN)
        t.append(f"{s.wins}  ", style=GREEN)
        t.append("L ", style=RED)
        t.append(f"{s.losses}\n", style=RED)

        t.append("  WIN RATE  ", style=DIM)
        t.append(f"{s.win_rate*100:.1f}%  ", style=_pct_color(s.win_rate - 0.5))
        t.append("  R:R  ", style=DIM)
        t.append(f"{s.avg_rr:.2f}", style=CYAN)

        return Panel(
            t,
            title=f"[{ORANGE}]◈ P & L[/{ORANGE}]",
            box=box.HEAVY_EDGE,
            style="grey7",
            padding=(0, 1),
        )

    # ------------------------------------------------------------------
    # Force-graph panel
    # ------------------------------------------------------------------

    def _force_graph_panel(self, s: BotState) -> Panel:
        field_val = max(-1.0, min(1.0, s.fg_field))
        conv_pct = s.fg_convergence * 100.0
        contradiction_pct = s.fg_contradiction * 100.0

        if field_val >= 0:
            bar = _force_bar(field_val)
            bar_line = Text()
            bar_line.append("BULL ", style=GREEN)
            bar_line.append("[", style=DIM)
            bar_line.append(bar, style=GREEN)
            bar_line.append("]", style=DIM)
            bar_line.append(" BEAR", style=DIM)
        else:
            bar = _force_bar(field_val)
            bar_line = Text()
            bar_line.append("BULL ", style=DIM)
            bar_line.append("[", style=DIM)
            bar_line.append(bar, style=RED)
            bar_line.append("]", style=DIM)
            bar_line.append(" BEAR", style=RED)

        t = Text()
        t.append_text(bar_line)
        t.append("\n")
        t.append("  Field: ", style=DIM)
        t.append(f"{_signed(field_val, 3)}  ", style=ORANGE)
        t.append("Conv: ", style=DIM)
        t.append(f"{conv_pct:.1f}%  ", style=CYAN)
        t.append("Contradict: ", style=DIM)
        t.append(f"{contradiction_pct:.1f}%\n", style=YELLOW)

        direction_color = GREEN if s.fg_direction == "BULL" else (RED if s.fg_direction == "BEAR" else DIM)
        t.append("  Signal: ", style=DIM)
        arrow = "▲" if s.fg_direction == "BULL" else ("▼" if s.fg_direction == "BEAR" else "─")
        t.append(f"{arrow}  {s.fg_direction}  ", style=f"bold {direction_color}")
        lag_color = RED if s.lag_active else GREEN
        t.append("  Lag Window: ", style=DIM)
        active_str = "ACTIVE" if s.lag_active else "idle"
        t.append(f"{active_str}  ", style=lag_color)
        t.append(f"(×{s.lag_windows_detected})", style=DIM)

        return Panel(
            t,
            title=f"[{ORANGE}]◈ FORCE-GRAPH[/{ORANGE}]",
            box=box.HEAVY_EDGE,
            style="grey7",
            padding=(0, 1),
        )

    # ------------------------------------------------------------------
    # Pipeline panel
    # ------------------------------------------------------------------

    def _pipeline_panel(self, s: BotState) -> Panel:
        stage = s.pipeline_stage  # 0=idle, 1-5 map to PIPELINE_STAGES

        t = Text()
        for i, name in enumerate(PIPELINE_STAGES, start=1):
            if stage == 0:
                style = DIM
                sym = "○"
            elif i < stage:
                style = GREEN
                sym = "●"
            elif i == stage:
                style = f"bold {ORANGE}"
                sym = "◉"
            else:
                style = DIM
                sym = "○"

            t.append(f" {sym} {name} ", style=style)
            if i < len(PIPELINE_STAGES):
                arrow_style = GREEN if (stage > 0 and i < stage) else DIM
                t.append("→", style=arrow_style)

        t.append("\n")

        # Stage label
        t.append("  Stage: ", style=DIM)
        if stage == 0:
            t.append("IDLE", style=DIM)
        else:
            label = PIPELINE_STAGES[stage - 1] if stage <= len(PIPELINE_STAGES) else "DONE"
            t.append(label, style=f"bold {ORANGE}")

        t.append("  │  Ticks/s: ", style=DIM)
        tps = s.btc_tick_count  # cumulative; display raw
        t.append(f"{tps:,}", style=CYAN)

        return Panel(
            t,
            title=f"[{ORANGE}]◈ PIPELINE[/{ORANGE}]",
            box=box.HEAVY_EDGE,
            style="grey7",
            padding=(0, 1),
        )

    # ------------------------------------------------------------------
    # Log panel
    # ------------------------------------------------------------------

    def _log_panel(self, s: BotState) -> Panel:
        t = Text()
        level_styles = {
            "INFO": "cyan",
            "WARN": "yellow",
            "ERROR": RED,
            "TRADE": GREEN,
            "HALT": f"bold {RED}",
        }
        for level, msg in list(s.log_lines):
            style = level_styles.get(level.upper(), DIM)
            t.append(f"[{level:5s}] ", style=style)
            t.append(f"{msg}\n", style="white")

        if not s.log_lines:
            t.append("  awaiting events…", style=DIM)

        return Panel(
            t,
            title=f"[{ORANGE}]◈ EVENT LOG[/{ORANGE}]",
            box=box.HEAVY_EDGE,
            style="grey7",
            padding=(0, 0),
        )

    # ------------------------------------------------------------------
    # Equity curve panel
    # ------------------------------------------------------------------

    def _equity_panel(self, s: BotState) -> Panel:
        history = s.equity_history
        spark = _sparkline(history, width=60)

        start = history[0] if history else s.capital_start
        end = history[-1] if history else s.capital
        delta = end - start
        delta_color = GREEN if delta >= 0 else RED

        t = Text()
        t.append("  ", style=DIM)
        t.append(spark, style=f"{'bright_green' if delta >= 0 else 'bright_red'}")
        t.append("\n")
        t.append(f"  Start: ${start:,.2f}  ", style=DIM)
        t.append(f"Now: ${end:,.2f}  ", style=BRIGHT_WHITE)
        t.append(f"Δ {_signed(delta)}", style=delta_color)
        t.append(f"  ({len(history)} samples)", style=DIM)

        # Mini drawdown calculation
        if len(history) >= 2:
            peak = max(history)
            trough = min(history[history.index(peak):]) if history.index(peak) < len(history) - 1 else end
            drawdown = (trough - peak) / peak * 100 if peak != 0 else 0.0
        else:
            drawdown = 0.0

        t.append("\n  Max Drawdown: ", style=DIM)
        t.append(f"{drawdown:.2f}%", style=RED if drawdown < -1 else DIM)

        return Panel(
            t,
            title=f"[{ORANGE}]◈ EQUITY CURVE[/{ORANGE}]",
            box=box.HEAVY_EDGE,
            style="grey7",
            padding=(0, 1),
        )

    # ------------------------------------------------------------------
    # Trades table panel
    # ------------------------------------------------------------------

    def _trades_panel(self, s: BotState) -> Panel:
        table = Table(
            box=box.SIMPLE_HEAVY,
            style="grey7",
            header_style=f"bold {ORANGE}",
            show_edge=False,
            expand=True,
            padding=(0, 1),
        )

        table.add_column("#", justify="right", style=DIM, width=4)
        table.add_column("DIR", justify="center", width=6)
        table.add_column("ENTRY", justify="right", width=10)
        table.add_column("EXIT", justify="right", width=10)
        table.add_column("BTC Δ", justify="right", width=9)
        table.add_column("P&L", justify="right", width=10)
        table.add_column("REPR", justify="center", width=5)
        table.add_column("✓/✗", justify="center", width=4)

        trades = list(s.recent_trades)[-8:]
        total = len(s.recent_trades)

        for i, trade in enumerate(reversed(trades), start=1):
            idx = total - i + 1
            direction = trade.get("direction", "?")
            entry = trade.get("entry", 0.0)
            exit_ = trade.get("exit", 0.0)
            pnl = trade.get("pnl", 0.0)
            repriced = trade.get("repriced", False)
            btc_move = trade.get("btc_move", 0.0)

            dir_style = GREEN if direction == "UP" else RED
            pnl_style = GREEN if pnl >= 0 else RED
            result_sym = "[bright_green]✓[/bright_green]" if pnl >= 0 else "[bright_red]✗[/bright_red]"
            row_style = "on grey11" if i % 2 == 0 else ""

            table.add_row(
                str(idx),
                Text(f"{'▲' if direction=='UP' else '▼'} {direction}", style=dir_style),
                f"${entry:.3f}",
                f"${exit_:.3f}",
                Text(f"{_signed(btc_move, 1)}", style=GREEN if btc_move >= 0 else RED),
                Text(f"{_signed(pnl, 2)}", style=pnl_style),
                Text("R" if repriced else "─", style=ORANGE if repriced else DIM),
                Text("✓" if pnl >= 0 else "✗", style="bright_green" if pnl >= 0 else "bright_red"),
                style=row_style,
            )

        if not trades:
            table.add_row("─", "─", "─", "─", "─", "─", "─", "─", style=DIM)

        return Panel(
            table,
            title=f"[{ORANGE}]◈ RECENT TRADES  (last {len(trades)} of {total})[/{ORANGE}]",
            box=box.HEAVY_EDGE,
            style="grey7",
            padding=(0, 0),
        )

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------

    def _footer_panel(self, s: BotState) -> Panel:
        # Edge / EV stats
        edge_style = GREEN if s.win_rate >= 0.55 else (YELLOW if s.win_rate >= 0.50 else RED)
        ev = (s.win_rate * s.avg_rr) - (1 - s.win_rate) if s.avg_rr > 0 else 0.0
        ev_style = GREEN if ev > 0 else RED

        # Conviction gate threshold display
        conv_gate_pct = s.fg_convergence * 100.0
        gate_met = s.fg_convergence >= 0.65
        gate_style = GREEN if gate_met else DIM
        gate_label = "OPEN" if gate_met else "CLOSED"

        # Spread / liquidity
        spread_style = GREEN if s.poly_spread_pct < 0.03 else (YELLOW if s.poly_spread_pct < 0.05 else RED)

        t = Text()
        t.append("  EDGE ", style=DIM)
        t.append(f"{s.win_rate*100:.1f}%  ", style=edge_style)
        t.append("│  EV ", style=DIM)
        t.append(f"{_signed(ev, 3)}  ", style=ev_style)
        t.append("│  CONV GATE ", style=DIM)
        t.append(f"{gate_label} ({conv_gate_pct:.1f}%)  ", style=gate_style)
        t.append("│  SPREAD ", style=DIM)
        t.append(f"{s.poly_spread_pct*100:.2f}%  ", style=spread_style)
        t.append("│  LIQUIDITY ", style=DIM)
        t.append(f"${s.poly_liquidity:,.0f}  ", style=CYAN)
        t.append("│  LAG WINDOWS ", style=DIM)
        t.append(f"×{s.lag_windows_detected}", style=ORANGE)
        t.append("\n")

        t.append("  MARKET: ", style=DIM)
        t.append(f"{s.market_name}  ", style=f"bold {ORANGE}")
        t.append("YES ", style=DIM)
        t.append(f"{s.poly_yes_price:.4f}  ", style=CYAN)
        t.append("NO ", style=DIM)
        t.append(f"{1 - s.poly_yes_price:.4f}  ", style=CYAN)
        t.append("│  TICKS PROCESSED: ", style=DIM)
        t.append(f"{s.btc_tick_count:,}", style=BRIGHT_WHITE)

        return Panel(
            t,
            style=f"bold {ORANGE}",
            box=box.HEAVY_EDGE,
            padding=(0, 1),
        )
