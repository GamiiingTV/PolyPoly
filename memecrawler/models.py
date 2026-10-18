"""
MemeCrawler — Structures de données
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Candidate:
    """Un coin tel que le crawler le voit (données DexScreener + RugCheck)."""
    mint: str
    symbol: str = ""
    name: str = ""
    pair_address: str = ""
    dex: str = ""
    created_at_ms: int = 0
    price_usd: float = 0.0
    price_native: float = 0.0
    quote_symbol: str = ""
    liquidity_usd: float = 0.0
    mcap_usd: float = 0.0
    volume_h24: float = 0.0
    volume_h1: float = 0.0
    trades_h24: int = 0
    buys_m5: int = 0
    sells_m5: int = 0
    buys_h1: int = 0
    sells_h1: int = 0
    change_m5: float = 0.0
    change_h1: float = 0.0
    change_h24: float = 0.0
    description: str = ""
    socials: list = field(default_factory=list)   # [{"type": "twitter", "url": ...}]
    websites: list = field(default_factory=list)
    chain: Optional["ChainReport"] = None

    def age_minutes(self, now_ms: int) -> float:
        if not self.created_at_ms:
            return 0.0
        return (now_ms - self.created_at_ms) / 60_000


@dataclass
class ChainReport:
    """Risque on-chain (RugCheck)."""
    top_wallet: float = 0.0      # part du plus gros wallet (0-1), pools exclues
    top_10: float = 0.0          # part cumulée du top 10 (0-1)
    holders: int = 0
    creator: str = ""
    creator_pct: float = 0.0     # part encore détenue par le dev (0-1)
    mint_authority: Optional[str] = None
    freeze_authority: Optional[str] = None
    rugged: bool = False
    insiders_detected: int = 0
    danger_risks: list = field(default_factory=list)  # noms des risques "danger"
    warn_risks: list = field(default_factory=list)


@dataclass
class Verdict:
    passed: bool
    stage: str            # free_kill | trade_kill | chain_kill | soft_kill | pick
    reason: str = ""
    retry: bool = False   # True = peut repasser plus tard (coin trop jeune, etc.)
