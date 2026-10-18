"""
MemeCrawler — Exécution des ordres (« FILLS »).

PaperExecutor : simulation (prix DexScreener réels, slippage + frais simulés).
LiveExecutor  : vrais swaps SOL ↔ token via Jupiter, signés avec ton wallet.
"""

import base64
import time
from dataclasses import dataclass
from typing import Optional

import httpx
from loguru import logger

from . import settings
from .models import Candidate
from .sources import WSOL
from .strategy import Position


@dataclass
class Fill:
    usd: float         # dépensé (achat) ou reçu (vente), net de frais
    qty: float         # tokens achetés / vendus
    qty_raw: int = 0
    price: float = 0.0
    signature: str = ""


class PaperExecutor:
    live = False

    def buy(self, c: Candidate, usd: float, sol_usd: float) -> Optional[Fill]:
        qty = usd * (1 - settings.PAPER_COST_PCT) / c.price_usd
        return Fill(usd=usd, qty=qty, price=usd / qty)

    def sell(self, pos: Position, c: Candidate, sol_usd: float) -> Optional[Fill]:
        usd = pos.qty * c.price_usd * (1 - settings.PAPER_COST_PCT)
        return Fill(usd=usd, qty=pos.qty, price=c.price_usd)


class LiveExecutor:
    live = True

    def __init__(self, http: httpx.Client):
        from solders.keypair import Keypair
        self.http = http
        self.kp = Keypair.from_base58_string(settings.SOLANA_PRIVATE_KEY)
        self.pubkey = str(self.kp.pubkey())

    # ---------- RPC ----------
    def _rpc(self, method: str, params: list):
        r = self.http.post(settings.SOLANA_RPC_URL,
                           json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        r.raise_for_status()
        d = r.json()
        if "error" in d:
            raise RuntimeError(f"RPC {method} : {d['error']}")
        return d["result"]

    def sol_balance(self) -> float:
        return self._rpc("getBalance", [self.pubkey, {"commitment": "confirmed"}])["value"] / 1e9

    def token_balance(self, mint: str) -> tuple[int, float]:
        res = self._rpc("getTokenAccountsByOwner", [
            self.pubkey, {"mint": mint}, {"encoding": "jsonParsed", "commitment": "confirmed"}])
        raw, ui = 0, 0.0
        for acc in res["value"]:
            amt = acc["account"]["data"]["parsed"]["info"]["tokenAmount"]
            raw += int(amt["amount"])
            ui += float(amt.get("uiAmount") or 0)
        return raw, ui

    # ---------- Jupiter ----------
    def _headers(self) -> dict:
        return {"x-api-key": settings.JUPITER_API_KEY} if settings.JUPITER_API_KEY else {}

    def _swap(self, input_mint: str, output_mint: str, amount_raw: int) -> Optional[str]:
        q = self.http.get(f"{settings.JUPITER_API_URL}/quote", headers=self._headers(), params={
            "inputMint": input_mint, "outputMint": output_mint,
            "amount": str(amount_raw), "slippageBps": settings.SLIPPAGE_BPS,
        })
        q.raise_for_status()
        quote = q.json()
        s = self.http.post(f"{settings.JUPITER_API_URL}/swap", headers=self._headers(), json={
            "quoteResponse": quote,
            "userPublicKey": self.pubkey,
            "wrapAndUnwrapSol": True,
            "dynamicComputeUnitLimit": True,
            "prioritizationFeeLamports": settings.PRIORITY_FEE_LAMPORTS,
        })
        s.raise_for_status()
        signed = sign_transaction(s.json()["swapTransaction"], self.kp)
        sig = self._rpc("sendTransaction", [signed, {
            "encoding": "base64", "skipPreflight": True, "maxRetries": 3}])
        return sig if self._confirm(sig) else None

    def _confirm(self, sig: str, timeout: float = 60) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            st = self._rpc("getSignatureStatuses", [[sig]])["value"][0]
            if st:
                if st.get("err"):
                    logger.error(f"Transaction échouée {sig} : {st['err']}")
                    return False
                if st.get("confirmationStatus") in ("confirmed", "finalized"):
                    return True
            time.sleep(2)
        logger.error(f"Transaction non confirmée après {timeout:.0f}s : {sig}")
        return False

    # ---------- Ordres ----------
    def buy(self, c: Candidate, usd: float, sol_usd: float) -> Optional[Fill]:
        lamports = int(usd / sol_usd * 1e9)
        if self.sol_balance() - lamports / 1e9 < settings.SOL_RESERVE:
            logger.warning("Pas assez de SOL (réserve de frais protégée)")
            return None
        before_raw, before_ui = self.token_balance(c.mint)
        try:
            sig = self._swap(WSOL, c.mint, lamports)
        except Exception as e:
            logger.error(f"Achat {c.symbol} échoué : {e}")
            return None
        if not sig:
            return None
        after_raw, after_ui = self.token_balance(c.mint)
        qty, qty_raw = after_ui - before_ui, after_raw - before_raw
        if qty_raw <= 0:
            logger.error(f"Achat {c.symbol} confirmé mais aucun token reçu ({sig})")
            return None
        return Fill(usd=usd, qty=qty, qty_raw=qty_raw, price=usd / qty, signature=sig)

    def sell(self, pos: Position, c: Candidate, sol_usd: float) -> Optional[Fill]:
        raw, ui = self.token_balance(pos.mint)
        if raw <= 0:
            logger.warning(f"Plus aucun token {pos.symbol} dans le wallet")
            return Fill(usd=0.0, qty=0.0)
        sol_before = self.sol_balance()
        try:
            sig = self._swap(pos.mint, WSOL, raw)
        except Exception as e:
            logger.error(f"Vente {pos.symbol} échouée : {e}")
            return None
        if not sig:
            return None
        usd = max(0.0, self.sol_balance() - sol_before) * sol_usd
        return Fill(usd=usd, qty=ui, qty_raw=raw, price=c.price_usd, signature=sig)


def sign_transaction(tx_b64: str, kp) -> str:
    """Signe la transaction renvoyée par Jupiter avec notre clé."""
    from solders.transaction import VersionedTransaction
    tx = VersionedTransaction.from_bytes(base64.b64decode(tx_b64))
    signed = VersionedTransaction(tx.message, [kp])
    return base64.b64encode(bytes(signed)).decode()
