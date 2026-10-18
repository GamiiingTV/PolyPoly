"""
MemeCrawler — Entrées / sorties.

Entrée : « no entry without a flush first »
  1. on suit le coin choisi et on mémorise son plus haut ;
  2. flush = baisse d'au moins FLUSH_PCT depuis ce plus haut ;
  3. on achète quand ça remonte de REBOUND_PCT depuis le creux
     ET que les acheteurs reviennent (plus d'achats que de ventes sur 5 min).
  Jamais si le coin a perdu plus de 50 % sur l'heure.

Sortie : stop loss, trailing stop, durée max, ou liquidité qui s'effondre.
"""

from dataclasses import dataclass, asdict
from typing import Optional

from . import settings
from .models import Candidate


@dataclass
class Watch:
    mint: str
    symbol: str
    picked_at: float
    peak: float
    trough: float = 0.0
    flushed: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass
class Position:
    mint: str
    symbol: str
    entry_price: float
    qty: float              # tokens (unités affichées)
    cost_usd: float
    opened_at: float
    entry_liquidity: float
    high: float
    qty_raw: int = 0        # unités brutes on-chain (mode live)

    def to_dict(self):
        return asdict(self)


def entry_signal(w: Watch, c: Candidate) -> Optional[str]:
    p = c.price_usd
    if p <= 0:
        return None
    if p > w.peak and not w.flushed:
        w.peak = p
    if c.change_h1 <= settings.MAX_H1_DROP:
        return None
    if not w.flushed and p <= w.peak * (1 - settings.FLUSH_PCT):
        w.flushed, w.trough = True, p
        return None
    if w.flushed:
        w.trough = min(w.trough, p)
        if p >= w.trough * (1 + settings.REBOUND_PCT) and c.buys_m5 > c.sells_m5:
            return (f"flush -{1 - w.trough / w.peak:.0%} puis rebond, "
                    f"acheteurs {c.buys_m5} vs vendeurs {c.sells_m5}")
    return None


def exit_signal(pos: Position, c: Candidate, now: float) -> Optional[str]:
    p = c.price_usd
    if p <= 0:
        return None
    pos.high = max(pos.high, p)
    pnl = p / pos.entry_price - 1
    if pnl <= -settings.STOP_LOSS:
        return f"stop loss {pnl:+.1%}"
    if pos.high >= pos.entry_price * (1 + settings.TRAIL_START) and p <= pos.high * (1 - settings.TRAIL_PCT):
        return f"trailing stop {pnl:+.1%} (plus haut {pos.high / pos.entry_price - 1:+.1%})"
    if pos.entry_liquidity and c.liquidity_usd < pos.entry_liquidity * (1 - settings.RUG_LIQ_DROP):
        return "liquidité qui s'effondre (rug ?)"
    if now - pos.opened_at > settings.MAX_HOLD_MIN * 60:
        return f"durée max atteinte {pnl:+.1%}"
    return None


def reset_after_exit(w: Watch, price: float):
    """Après une sortie on repart de zéro : il faudra un nouveau flush."""
    w.peak, w.trough, w.flushed = price, 0.0, False
