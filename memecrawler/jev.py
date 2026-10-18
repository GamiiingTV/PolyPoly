"""
MemeCrawler — Jev, le mini juge IA.

Il ne fait que noter le coin (6 scores entre 0 et 1) et dire oui ou non.
Les seuils SOFT décident ensuite (filters.soft_kill) : Jev ne peut pas
faire passer un coin que les chiffres refusent.
"""

import json
from typing import Optional

import anthropic
from loguru import logger
from pydantic import BaseModel

from . import settings
from .models import Candidate

SYSTEM = """Tu es Jev, le juge d'un desk de trading de memecoins Solana.
On te donne un coin qui a déjà passé les filtres chiffrés (âge, liquidité, volume, holders).
Ton rôle : repérer les arnaques (rug pulls) et les coins où il est trop tard.

Note chaque critère entre 0.0 et 1.0 :
- concentration_is_exit_risk : risque que les gros holders/insiders vendent sur nous (1 = très probable).
- momentum_already_spent : le pump est déjà fini, on arriverait en haut (1 = complètement fini).
- liquidity_fits_ticket : la liquidité permet d'entrer ET de sortir avec notre ticket sans gros slippage (1 = parfait).
- account_is_the_project : les liens/réseaux sociaux semblent appartenir à CE projet, pas un compte volé ou générique (1 = certain). Aucun réseau social = 0.3 maximum.
- recycled_account : compte X ou site recyclé d'un ancien projet / rebrandé (1 = certain).
- dev_still_loaded : le dev détient encore une part qui peut être dumpée (1 = très chargé).

verdict = true seulement si tu achèterais ce coin. Sois strict : la plupart des nouveaux coins sont des arnaques.
reason : une phrase courte en français."""


class JevAnswer(BaseModel):
    concentration_is_exit_risk: float
    momentum_already_spent: float
    liquidity_fits_ticket: float
    account_is_the_project: float
    recycled_account: float
    dev_still_loaded: float
    verdict: bool
    reason: str


def describe(c: Candidate, ticket_usd: float, now_ms: int) -> str:
    r = c.chain
    data = {
        "symbol": c.symbol, "name": c.name, "dex": c.dex,
        "age_minutes": round(c.age_minutes(now_ms)),
        "price_usd": c.price_usd, "market_cap_usd": round(c.mcap_usd),
        "liquidity_usd": round(c.liquidity_usd), "our_ticket_usd": round(ticket_usd, 2),
        "volume_h24_usd": round(c.volume_h24), "volume_h1_usd": round(c.volume_h1),
        "trades_h24": c.trades_h24,
        "buys_sells_m5": [c.buys_m5, c.sells_m5], "buys_sells_h1": [c.buys_h1, c.sells_h1],
        "price_change_pct": {"m5": c.change_m5, "h1": c.change_h1, "h24": c.change_h24},
        "description": c.description[:500],
        "socials": c.socials, "websites": c.websites,
    }
    if r:
        data["onchain"] = {
            "holders": r.holders, "top_wallet_pct": round(r.top_wallet * 100, 2),
            "top10_pct": round(r.top_10 * 100, 2), "dev_holds_pct": round(r.creator_pct * 100, 2),
            "insiders_detected": r.insiders_detected, "warnings": r.warn_risks,
        }
    return json.dumps(data, ensure_ascii=False)


class Jev:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY or None)

    def judge(self, c: Candidate, ticket_usd: float, now_ms: int) -> Optional[JevAnswer]:
        try:
            resp = self.client.messages.parse(
                model=settings.JEV_MODEL,
                max_tokens=4096,
                system=SYSTEM,
                messages=[{"role": "user", "content": describe(c, ticket_usd, now_ms)}],
                output_format=JevAnswer,
            )
        except anthropic.APIStatusError as e:
            logger.warning(f"Jev erreur API {e.status_code} : {e.message}")
            return None
        except anthropic.APIConnectionError:
            logger.warning("Jev injoignable")
            return None
        if resp.stop_reason != "end_turn" or resp.parsed_output is None:
            logger.warning(f"Jev sans réponse exploitable ({resp.stop_reason})")
            return None
        a = resp.parsed_output
        for k in JevAnswer.model_fields:
            v = getattr(a, k)
            if isinstance(v, float):
                setattr(a, k, min(1.0, max(0.0, v)))
        return a
