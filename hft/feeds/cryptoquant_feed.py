"""
HFT Feed CryptoQuant — Flux d'exchanges BTC.

Données récupérées (polling REST toutes les 5min) :
  • Exchange Net Position Change  → sortie nette = bullish
  • Exchange Inflow/Outflow       → inflow élevé = bearish
  • Miner to Exchange Flow        → pression de vente
  • Fund Flow                     → flux institutionnels

Sans clé API : utilise CoinGlass (public) comme fallback.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx
from loguru import logger

from hft.config_hft import (
    CRYPTOQUANT_API_KEY,
    CRYPTOQUANT_BASE_URL,
    CRYPTOQUANT_POLL_SEC,
)


# ── Structures ────────────────────────────────────────────────────────────────

@dataclass
class ExchangeFlowData:
    """Données de flux d'exchanges normalisées en signal [-1, +1]."""

    # Flux nets : sortie > 0 = bullish (coins quittent les exchanges)
    net_position_change: float = 0.0     # Variation position nette exchange
    inflow_signal: float = 0.0           # -1 (fort inflow=bear) → +1 (faible)
    outflow_signal: float = 0.0          # +1 (fort outflow=bull)
    miner_outflow_signal: float = 0.0    # Vente mineurs : -1 = bear

    # Données brutes pour log / debug
    inflow_usd: float = 0.0
    outflow_usd: float = 0.0
    net_flow_usd: float = 0.0

    # Funding rate (perp Binance) : négatif = bears paient longs
    funding_rate: float = 0.0            # signal : positif = longs dominent
    open_interest_change_pct: float = 0.0

    # Long/short ratio (contrarian)
    long_short_ratio: float = 1.0        # >1 = plus de longs

    timestamp: int = field(default_factory=lambda: int(time.time()))
    source: str = "none"
    stale: bool = True


# ── Client CryptoQuant ────────────────────────────────────────────────────────

class CryptoQuantFeed:
    """
    Récupère les données on-chain / exchange flows depuis CryptoQuant.

    Fallback vers Binance public API pour funding rate et OI si pas de clé.
    """

    BINANCE_FUNDING_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
    BINANCE_OI_URL = "https://fapi.binance.com/fapi/v1/openInterest"
    BINANCE_LS_URL = "https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
    COINGLASS_FUNDING = "https://open-api.coinglass.com/public/v2/funding"

    def __init__(self) -> None:
        self._data = ExchangeFlowData()
        self._running = False
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_connections=10, keepalive_expiry=30),
        )
        self._has_cq_key = bool(CRYPTOQUANT_API_KEY)

    def get_latest(self) -> ExchangeFlowData:
        return self._data

    def is_fresh(self) -> bool:
        age = time.time() - self._data.timestamp
        return age < CRYPTOQUANT_POLL_SEC * 2 and not self._data.stale

    # ── Boucle principale ─────────────────────────────────────────────────────

    async def run_forever(self) -> None:
        self._running = True
        logger.info(
            f"CryptoQuant Feed démarré "
            f"({'avec clé API' if self._has_cq_key else 'fallback Binance/public'})"
        )
        # Premier fetch immédiat
        await self._fetch_all()
        while self._running:
            await asyncio.sleep(CRYPTOQUANT_POLL_SEC)
            await self._fetch_all()

    def stop(self) -> None:
        self._running = False

    # ── Fetch principal ───────────────────────────────────────────────────────

    async def _fetch_all(self) -> None:
        tasks = [self._fetch_binance_derivatives()]
        if self._has_cq_key:
            tasks.append(self._fetch_cryptoquant_flows())
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                logger.debug(f"CryptoQuant fetch erreur: {r}")

    # ── Binance Derivatives (funding rate, OI, L/S ratio) — Public ───────────

    async def _fetch_binance_derivatives(self) -> None:
        try:
            funding_task = self._http.get(
                self.BINANCE_FUNDING_URL,
                params={"symbol": "BTCUSDT", "limit": 1},
            )
            oi_task = self._http.get(
                self.BINANCE_OI_URL,
                params={"symbol": "BTCUSDT"},
            )
            ls_task = self._http.get(
                self.BINANCE_LS_URL,
                params={"symbol": "BTCUSDT", "period": "5m", "limit": 2},
            )
            funding_resp, oi_resp, ls_resp = await asyncio.gather(
                funding_task, oi_task, ls_task,
                return_exceptions=True,
            )

            # Funding rate
            if not isinstance(funding_resp, Exception):
                funding_resp.raise_for_status()
                data = funding_resp.json()
                if data:
                    fr = float(data[-1].get("fundingRate", 0))
                    # Normalise : [-0.01%, +0.01%] → [-1, +1]
                    self._data.funding_rate = max(-1.0, min(1.0, fr / 0.0001))

            # Open Interest change
            if not isinstance(oi_resp, Exception):
                oi_resp.raise_for_status()
                oi_data = oi_resp.json()
                oi_val = float(oi_data.get("openInterest", 0))
                # OI change en % (estimé vs dernière valeur)
                self._data.open_interest_change_pct = oi_val

            # Long/Short ratio
            if not isinstance(ls_resp, Exception):
                ls_resp.raise_for_status()
                ls_data = ls_resp.json()
                if len(ls_data) >= 2:
                    old_ls = float(ls_data[0].get("longShortRatio", 1))
                    new_ls = float(ls_data[1].get("longShortRatio", 1))
                    self._data.long_short_ratio = new_ls
                    # Contrarian : trop de longs = signal baissier (on normalise)
                    # ratio = 1.5 → signal = -0.5 (beaucoup de longs = danger)
                    self._data.outflow_signal = max(-1.0, min(1.0, 2 - new_ls))

            self._data.timestamp = int(time.time())
            self._data.stale = False
            self._data.source = "binance_derivatives"

        except Exception as e:
            logger.debug(f"Binance derivatives fetch: {e}")

    # ── CryptoQuant API (avec clé) ────────────────────────────────────────────

    async def _fetch_cryptoquant_flows(self) -> None:
        headers = {"Authorization": f"Bearer {CRYPTOQUANT_API_KEY}"}
        try:
            # Exchange Net Position Change
            resp = await self._http.get(
                f"{CRYPTOQUANT_BASE_URL}/btc/exchange-flows/netflow",
                headers=headers,
                params={"window": "hour", "limit": 3},
            )
            if resp.status_code == 200:
                data = resp.json().get("result", {}).get("data", [])
                if data:
                    latest = data[-1]
                    netflow = float(latest.get("netflow_total", 0))
                    # Netflow négatif = sortie des exchanges = bullish
                    # On normalise : ±5000 BTC/h → [-1, +1]
                    self._data.net_position_change = max(
                        -1.0, min(1.0, -netflow / 5000.0)
                    )

            # Inflow / Outflow
            resp2 = await self._http.get(
                f"{CRYPTOQUANT_BASE_URL}/btc/exchange-flows/inflow",
                headers=headers,
                params={"window": "hour", "limit": 3},
            )
            if resp2.status_code == 200:
                data2 = resp2.json().get("result", {}).get("data", [])
                if data2:
                    latest2 = data2[-1]
                    inflow = float(latest2.get("inflow_total", 0))
                    # Inflow élevé = bearish
                    self._data.inflow_usd = inflow
                    self._data.inflow_signal = max(-1.0, min(1.0, -inflow / 3000.0))

            self._data.source = "cryptoquant"
            logger.debug(
                f"CryptoQuant: netflow={self._data.net_position_change:.3f} "
                f"inflow={self._data.inflow_signal:.3f}"
            )

        except Exception as e:
            logger.debug(f"CryptoQuant API erreur: {e}")

    async def close(self) -> None:
        self.stop()
        await self._http.aclose()
