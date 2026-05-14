"""
HFT Executor — Exécution d'ordres Polymarket en <100ms.

Pipeline d'exécution :
  T+0ms   Signal détecté (force-graph convergé + lag ouvert)
  T+5ms   Vérification risque (RiskManager)
  T+15ms  Construction ordre
  T+20ms  Signature HMAC (CLOBAuth)
  T+50ms  Envoi HTTP POST (connexion keep-alive pré-établie)
  T+80ms  Réponse reçue

Architecture :
  - Connection pool persistent (pas de TCP handshake à chaque ordre)
  - Pre-computed auth headers template (seul le timestamp change)
  - Async non-bloquant tout le pipeline
  - Circuit-breaker intégré (10 échecs consécutifs → pause 60s)
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Optional

import aiohttp
from loguru import logger

from hft.config_hft import (
    CLOB_REST_URL,
    HTTP_TIMEOUT_SEC,
    MAX_EXECUTION_MS,
    POLY_RATE_LIMIT_PER_SEC,
)
from hft.execution.lag_detector import EdgeWindow
from hft.risk.risk_manager import RiskManager, TradeSignal


# ── Structures ────────────────────────────────────────────────────────────────

@dataclass
class OrderResult:
    success: bool
    order_id: Optional[str]
    token_id: str
    side: str
    amount_usd: float
    price: float
    execution_ms: float
    error: Optional[str] = None
    timestamp_ms: int = 0

    def __post_init__(self):
        if not self.timestamp_ms:
            self.timestamp_ms = int(time.time() * 1000)


# ── Circuit Breaker ────────────────────────────────────────────────────────────

class CircuitBreaker:
    def __init__(self, max_failures: int = 10, reset_sec: float = 60.0) -> None:
        self._failures = 0
        self._max = max_failures
        self._tripped_at: float = 0.0
        self._reset_sec = reset_sec

    def record_success(self) -> None:
        self._failures = 0

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._max:
            self._tripped_at = time.time()
            logger.error(
                f"Circuit breaker ouvert : {self._failures} échecs consécutifs"
            )

    def is_open(self) -> bool:
        if self._failures < self._max:
            return False
        if time.time() - self._tripped_at > self._reset_sec:
            self._failures = 0
            logger.info("Circuit breaker réinitialisé")
            return False
        return True


# ── Rate Limiter ──────────────────────────────────────────────────────────────

class RateLimiter:
    """Token bucket — limite les ordres par seconde."""

    def __init__(self, rate: int = POLY_RATE_LIMIT_PER_SEC) -> None:
        self._rate = rate
        self._tokens = float(rate)
        self._last_refill = time.monotonic()

    async def acquire(self) -> bool:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._rate, self._tokens + elapsed * self._rate)
        self._last_refill = now

        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True

        wait = (1.0 - self._tokens) / self._rate
        await asyncio.sleep(wait)
        self._tokens = 0.0
        return True


# ── CLOB Auth ─────────────────────────────────────────────────────────────────

class FastCLOBAuth:
    """Authentification CLOB ultra-rapide (HMAC pré-compilé)."""

    def __init__(self) -> None:
        import base64
        import os
        self._api_key = os.getenv("POLYMARKET_API_KEY", "")
        secret_raw = os.getenv("POLYMARKET_API_SECRET", "")
        passphrase = os.getenv("POLYMARKET_API_PASSPHRASE", "")
        self._passphrase = passphrase

        try:
            self._secret_bytes = base64.b64decode(secret_raw) if secret_raw else b""
        except Exception:
            self._secret_bytes = b""

    def make_headers(self, method: str, path: str, body: str = "") -> dict:
        import hmac
        import hashlib
        import base64

        ts = str(int(time.time() * 1000))
        message = ts + method.upper() + path + body
        mac = hmac.new(
            self._secret_bytes,
            message.encode("utf-8"),
            hashlib.sha256,
        )
        sig = base64.b64encode(mac.digest()).decode("utf-8")
        return {
            "POLY-API-KEY": self._api_key,
            "POLY-SIGNATURE": sig,
            "POLY-TIMESTAMP": ts,
            "POLY-PASSPHRASE": self._passphrase,
            "Content-Type": "application/json",
        }

    @property
    def configured(self) -> bool:
        return bool(self._api_key and self._secret_bytes)


# ── Executor principal ────────────────────────────────────────────────────────

class HFTExecutor:
    """
    Exécute des ordres sur le CLOB Polymarket en <100ms.

    Mode simulation : si les clés API ne sont pas configurées,
    logue l'ordre sans l'envoyer réellement.
    """

    def __init__(self, risk_manager: RiskManager) -> None:
        self.risk = risk_manager
        self._auth = FastCLOBAuth()
        self._circuit_breaker = CircuitBreaker()
        self._rate_limiter = RateLimiter()

        # Session aiohttp persistante (connexion keep-alive vers Polymarket)
        connector = aiohttp.TCPConnector(
            limit=50,
            limit_per_host=20,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
            force_close=False,
        )
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector = connector

        self._live_mode = self._auth.configured
        self._order_count = 0
        self._total_executed_usd = 0.0

    async def start(self) -> None:
        """Ouvre la session HTTP persistante."""
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SEC)
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            timeout=timeout,
            headers={"User-Agent": "PolyPolyHFT/2.0"},
        )
        mode = "LIVE" if self._live_mode else "SIMULATION"
        logger.info(f"HFT Executor démarré — mode {mode}")

    async def close(self) -> None:
        if self._session:
            await self._session.close()

    # ── Exécution principale ──────────────────────────────────────────────────

    async def execute(
        self,
        token_id: str,
        side: str,          # "BUY"
        amount_usd: float,
        price: float,       # Prix limite (0.0 → 1.0)
        market_id: str = "",
    ) -> OrderResult:
        """
        Place un ordre sur le CLOB Polymarket.

        Returns:
            OrderResult avec timing d'exécution.
        """
        start_ns = time.perf_counter_ns()

        # Circuit breaker
        if self._circuit_breaker.is_open():
            return OrderResult(
                success=False, order_id=None,
                token_id=token_id, side=side,
                amount_usd=amount_usd, price=price,
                execution_ms=0.0,
                error="circuit_breaker_open",
            )

        # Rate limiting
        await self._rate_limiter.acquire()

        # Construction du corps de l'ordre
        order_body = {
            "orderType": "LIMIT",
            "tokenID": token_id,
            "side": side,
            "price": str(round(price, 4)),
            "size": str(round(amount_usd / price, 2)) if price > 0 else "0",
            "timeInForce": "FOK",    # Fill or Kill pour HFT
        }
        body_str = json.dumps(order_body, separators=(",", ":"))
        path = "/order"

        if not self._live_mode:
            # Mode simulation
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            result = OrderResult(
                success=True,
                order_id=f"SIM-{self._order_count:06d}",
                token_id=token_id,
                side=side,
                amount_usd=amount_usd,
                price=price,
                execution_ms=elapsed_ms,
            )
            self._order_count += 1
            self._total_executed_usd += amount_usd
            logger.info(
                f"[SIM] Ordre #{self._order_count}: {side} ${amount_usd:.2f} "
                f"@ {price:.4f} | {elapsed_ms:.1f}ms"
            )
            return result

        # Live mode
        headers = self._auth.make_headers("POST", path, body_str)
        try:
            async with self._session.post(
                f"{CLOB_REST_URL}{path}",
                data=body_str,
                headers=headers,
            ) as resp:
                elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
                resp_text = await resp.text()

                if resp.status == 200:
                    data = json.loads(resp_text)
                    order_id = data.get("orderID") or data.get("id", "")
                    self._circuit_breaker.record_success()
                    self._order_count += 1
                    self._total_executed_usd += amount_usd

                    if elapsed_ms > MAX_EXECUTION_MS:
                        logger.warning(
                            f"Latence élevée: {elapsed_ms:.1f}ms > {MAX_EXECUTION_MS}ms"
                        )
                    else:
                        logger.info(
                            f"Ordre exécuté: {side} ${amount_usd:.2f} "
                            f"@ {price:.4f} | {elapsed_ms:.1f}ms | id={order_id[:8]}"
                        )
                    return OrderResult(
                        success=True,
                        order_id=order_id,
                        token_id=token_id,
                        side=side,
                        amount_usd=amount_usd,
                        price=price,
                        execution_ms=elapsed_ms,
                    )
                else:
                    self._circuit_breaker.record_failure()
                    logger.warning(
                        f"Ordre rejeté [{resp.status}]: {resp_text[:200]}"
                    )
                    return OrderResult(
                        success=False,
                        order_id=None,
                        token_id=token_id,
                        side=side,
                        amount_usd=amount_usd,
                        price=price,
                        execution_ms=elapsed_ms,
                        error=f"http_{resp.status}",
                    )

        except asyncio.TimeoutError:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            self._circuit_breaker.record_failure()
            logger.warning(f"Timeout ordre après {elapsed_ms:.0f}ms")
            return OrderResult(
                success=False, order_id=None,
                token_id=token_id, side=side,
                amount_usd=amount_usd, price=price,
                execution_ms=elapsed_ms, error="timeout",
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            self._circuit_breaker.record_failure()
            logger.error(f"Erreur exécution: {e}")
            return OrderResult(
                success=False, order_id=None,
                token_id=token_id, side=side,
                amount_usd=amount_usd, price=price,
                execution_ms=elapsed_ms, error=str(e),
            )

    # ── Exécution trade directionnel ──────────────────────────────────────────

    async def execute_directional(
        self,
        market,             # BTCMarket
        signal: TradeSignal,
        edge_window: EdgeWindow,
    ) -> Optional[OrderResult]:
        """
        Place un ordre dans la direction du signal.

        BULL → BUY YES token
        BEAR → BUY NO token (= vendre la hausse)
        """
        if signal.direction == "BULL":
            token_id = market.token_id_yes
            price = market.yes_ask   # On achète au meilleur ask
        else:
            token_id = market.token_id_no
            price = market.no_ask

        if price <= 0 or price >= 1:
            logger.debug(f"Prix invalide pour ordre: {price}")
            return None

        result = await self.execute(
            token_id=token_id,
            side="BUY",
            amount_usd=signal.size_usd,
            price=price,
            market_id=market.market_id,
        )

        if result.success:
            self.risk.record_order_placed(signal, result)

        return result

    @property
    def stats(self) -> dict:
        return {
            "orders_executed": self._order_count,
            "total_usd_executed": self._total_executed_usd,
            "live_mode": self._live_mode,
            "circuit_open": self._circuit_breaker.is_open(),
        }
