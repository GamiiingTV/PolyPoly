"""
MemeCrawler — Sources de données (gratuites, sans clé)

- DexScreener : nouveaux coins + prix/liquidité/volume/transactions
- RugCheck    : holders, dev, autorités, risques on-chain
"""

from typing import Optional

import httpx
from loguru import logger

from .models import Candidate, ChainReport

DEX_URL = "https://api.dexscreener.com"
RUGCHECK_URL = "https://api.rugcheck.xyz/v1"
WSOL = "So11111111111111111111111111111111111111112"


def _num(x, default=0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


class DexScreener:
    def __init__(self, http: httpx.Client):
        self.http = http

    def latest_solana_mints(self) -> list[dict]:
        """Coins récemment apparus (profils + boosts) sur Solana."""
        found: dict[str, dict] = {}
        for path in ("/token-profiles/latest/v1", "/token-boosts/latest/v1"):
            try:
                r = self.http.get(DEX_URL + path)
                r.raise_for_status()
                items = r.json()
            except Exception as e:
                logger.warning(f"DexScreener {path} : {e}")
                continue
            if isinstance(items, dict):
                items = [items]
            for it in items:
                if it.get("chainId") == "solana" and it.get("tokenAddress"):
                    found.setdefault(it["tokenAddress"], it)
        return list(found.values())

    def candidates(self, mints: list[str]) -> dict[str, Candidate]:
        """Meilleure paire (plus grosse liquidité) pour chaque mint, par lots de 30."""
        out: dict[str, Candidate] = {}
        for i in range(0, len(mints), 30):
            batch = mints[i:i + 30]
            try:
                r = self.http.get(f"{DEX_URL}/tokens/v1/solana/{','.join(batch)}")
                r.raise_for_status()
                pairs = r.json() or []
            except Exception as e:
                logger.warning(f"DexScreener tokens : {e}")
                continue
            for p in pairs:
                mint = (p.get("baseToken") or {}).get("address")
                if mint not in batch:
                    continue
                c = parse_pair(p)
                if mint not in out or c.liquidity_usd > out[mint].liquidity_usd:
                    out[mint] = c
        return out

    def sol_usd(self) -> float:
        best = self.candidates([WSOL]).get(WSOL)
        return best.price_usd if best else 0.0


def parse_pair(p: dict) -> Candidate:
    base = p.get("baseToken") or {}
    txns = p.get("txns") or {}
    vol = p.get("volume") or {}
    chg = p.get("priceChange") or {}
    info = p.get("info") or {}
    h24 = txns.get("h24") or {}
    return Candidate(
        mint=base.get("address", ""),
        symbol=base.get("symbol", ""),
        name=base.get("name", ""),
        pair_address=p.get("pairAddress", ""),
        dex=p.get("dexId", ""),
        created_at_ms=int(p.get("pairCreatedAt") or 0),
        price_usd=_num(p.get("priceUsd")),
        price_native=_num(p.get("priceNative")),
        quote_symbol=(p.get("quoteToken") or {}).get("symbol", ""),
        liquidity_usd=_num((p.get("liquidity") or {}).get("usd")),
        mcap_usd=_num(p.get("marketCap") or p.get("fdv")),
        volume_h24=_num(vol.get("h24")),
        volume_h1=_num(vol.get("h1")),
        trades_h24=int(_num(h24.get("buys")) + _num(h24.get("sells"))),
        buys_m5=int(_num((txns.get("m5") or {}).get("buys"))),
        sells_m5=int(_num((txns.get("m5") or {}).get("sells"))),
        buys_h1=int(_num((txns.get("h1") or {}).get("buys"))),
        sells_h1=int(_num((txns.get("h1") or {}).get("sells"))),
        change_m5=_num(chg.get("m5")),
        change_h1=_num(chg.get("h1")),
        change_h24=_num(chg.get("h24")),
        socials=info.get("socials") or [],
        websites=info.get("websites") or [],
    )


class RugCheck:
    def __init__(self, http: httpx.Client):
        self.http = http

    def report(self, mint: str) -> Optional[ChainReport]:
        try:
            r = self.http.get(f"{RUGCHECK_URL}/tokens/{mint}/report")
            r.raise_for_status()
            return parse_report(r.json())
        except Exception as e:
            logger.warning(f"RugCheck {mint[:8]} : {e}")
            return None


def parse_report(d: dict) -> ChainReport:
    # Comptes des pools de liquidité : ce ne sont pas des « wallets »
    pool_accounts: set[str] = set()
    for m in d.get("markets") or []:
        for k in ("pubkey", "liquidityA", "liquidityB", "liquidityAAccount", "liquidityBAccount"):
            v = m.get(k)
            if isinstance(v, str):
                pool_accounts.add(v)
            elif isinstance(v, dict):
                pool_accounts.update(x for x in (v.get("pubkey"), v.get("owner")) if x)

    holders = []
    for h in d.get("topHolders") or []:
        if h.get("address") in pool_accounts or h.get("owner") in pool_accounts:
            continue
        holders.append(_num(h.get("pct")) / 100)
    holders.sort(reverse=True)

    supply = _num((d.get("token") or {}).get("supply"))
    creator_balance = _num(d.get("creatorBalance"))
    risks = d.get("risks") or []
    return ChainReport(
        top_wallet=holders[0] if holders else 0.0,
        top_10=sum(holders[:10]),
        holders=int(_num(d.get("totalHolders"))),
        creator=d.get("creator") or "",
        creator_pct=(creator_balance / supply) if supply else 0.0,
        mint_authority=d.get("mintAuthority") or (d.get("token") or {}).get("mintAuthority"),
        freeze_authority=d.get("freezeAuthority") or (d.get("token") or {}).get("freezeAuthority"),
        rugged=bool(d.get("rugged")),
        insiders_detected=int(_num(d.get("graphInsidersDetected"))),
        danger_risks=[r.get("name", "") for r in risks if r.get("level") == "danger"],
        warn_risks=[r.get("name", "") for r in risks if r.get("level") == "warn"],
    )
