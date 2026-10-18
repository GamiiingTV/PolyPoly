"""
MemeCrawler — filter.py : l'ordre EST tout l'intérêt.

free_kill → trade_kill → chain_kill → soft_kill → pick

On tue d'abord avec ce qui ne coûte rien (données déjà chargées),
puis on paie un appel RugCheck, et Jev (l'IA) seulement pour les survivants.
"""

from typing import Optional

from .models import Candidate, ChainReport, Verdict
from .thresholds import HARD, SOFT


def free_kill(c: Candidate, now_ms: int) -> Optional[Verdict]:
    age = c.age_minutes(now_ms)
    if age < HARD["min_age_minutes"]:
        return Verdict(False, "free_kill", f"trop jeune ({age:.0f} min)", retry=True)
    if c.liquidity_usd < HARD["min_liquidity_usd"]:
        return Verdict(False, "free_kill", f"liquidité {c.liquidity_usd:,.0f} $", retry=True)
    if c.mcap_usd < HARD["min_mcap_usd"]:
        return Verdict(False, "free_kill", f"mcap {c.mcap_usd:,.0f} $", retry=True)
    return None


def trade_kill(c: Candidate) -> Optional[Verdict]:
    if c.volume_h24 < HARD["min_volume_h24"]:
        return Verdict(False, "trade_kill", f"volume 24h {c.volume_h24:,.0f} $", retry=True)
    if c.trades_h24 < HARD["min_trades_h24"]:
        return Verdict(False, "trade_kill", f"{c.trades_h24} trades 24h", retry=True)
    return None


def chain_kill(r: Optional[ChainReport]) -> Optional[Verdict]:
    if r is None:
        return Verdict(False, "chain_kill", "rapport on-chain indisponible", retry=True)
    if r.rugged:
        return Verdict(False, "chain_kill", "déjà rug")
    if r.mint_authority:
        return Verdict(False, "chain_kill", "le dev peut encore minter")
    if r.freeze_authority:
        return Verdict(False, "chain_kill", "le dev peut geler les wallets")
    if r.top_wallet > HARD["max_top_wallet"]:
        return Verdict(False, "chain_kill", f"top wallet {r.top_wallet:.1%}")
    if r.top_10 > HARD["max_top_10"]:
        return Verdict(False, "chain_kill", f"top 10 {r.top_10:.1%}")
    if r.danger_risks:
        return Verdict(False, "chain_kill", "risque : " + ", ".join(r.danger_risks[:3]))
    return None


def soft_kill(scores: dict[str, float]) -> Optional[Verdict]:
    """Applique les seuils SOFT aux réponses de Jev."""
    for name, (kind, limit) in SOFT.items():
        v = scores.get(name)
        if v is None:
            return Verdict(False, "soft_kill", f"{name} manquant")
        if (kind == "max" and v > limit) or (kind == "min" and v < limit):
            return Verdict(False, "soft_kill", f"{name} = {v:.2f} ({kind} {limit})")
    return None
