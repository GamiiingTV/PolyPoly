"""
MemeCrawler — État persistant (bank, position, picks, historique).
"""

import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional

from . import settings
from .strategy import Position, Watch


@dataclass
class State:
    bank_usd: float = 0.0                 # bank papier (en live : solde réel lu on-chain)
    position: Optional[Position] = None
    watches: dict = field(default_factory=dict)       # mint → Watch
    seen: dict = field(default_factory=dict)          # mint → {"first": ts, "next": ts|None}
    trades: list = field(default_factory=list)
    day: str = ""
    day_pnl: float = 0.0
    stats: dict = field(default_factory=lambda: {"scanned": 0, "killed": {}, "picks": 0})

    def record_kill(self, stage: str):
        k = self.stats.setdefault("killed", {})
        k[stage] = k.get(stage, 0) + 1

    def roll_day(self):
        today = time.strftime("%Y-%m-%d", time.gmtime())
        if today != self.day:
            self.day, self.day_pnl = today, 0.0

    def save(self):
        settings.DATA_DIR.mkdir(exist_ok=True)
        data = {
            "bank_usd": self.bank_usd,
            "position": self.position.to_dict() if self.position else None,
            "watches": {m: w.to_dict() for m, w in self.watches.items()},
            "seen": self.seen, "trades": self.trades[-500:],
            "day": self.day, "day_pnl": self.day_pnl, "stats": self.stats,
        }
        tmp = settings.STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1))
        os.replace(tmp, settings.STATE_FILE)

    @classmethod
    def load(cls) -> "State":
        if not settings.STATE_FILE.exists():
            return cls(bank_usd=settings.PAPER_BANK_USD)
        d = json.loads(settings.STATE_FILE.read_text())
        return cls(
            bank_usd=d.get("bank_usd", settings.PAPER_BANK_USD),
            position=Position(**d["position"]) if d.get("position") else None,
            watches={m: Watch(**w) for m, w in (d.get("watches") or {}).items()},
            seen=d.get("seen") or {}, trades=d.get("trades") or [],
            day=d.get("day", ""), day_pnl=d.get("day_pnl", 0.0),
            stats=d.get("stats") or {"scanned": 0, "killed": {}, "picks": 0},
        )
