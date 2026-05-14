"""
HFT TradingView Signals — Agrège les recommandations TradingView pour BTCUSDT 5M.

Utilise la bibliothèque tradingview-ta (scraping public, sans clé API).
Polling toutes les 30 secondes avec cache et gestion des timeouts.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

from loguru import logger

from hft.config_hft import (
    TV_EXCHANGE,
    TV_SYMBOL,
    TV_SCREENER,
    TV_POLL_SEC,
    TV_TIMEOUT_SEC,
)

try:
    from tradingview_ta import TA_Handler, Interval
    TV_AVAILABLE = True
except ImportError:
    TV_AVAILABLE = False
    logger.warning("tradingview-ta non installé — signaux TV désactivés")


# ── Structures ────────────────────────────────────────────────────────────────

@dataclass
class TVSignals:
    """Signaux TradingView normalisés [-1, +1]."""

    # Recommandation globale
    recommendation: float = 0.0         # STRONG_BUY=+1 → STRONG_SELL=-1

    # Oscillateurs (RSI, Stoch, MACD, CCI…)
    oscillators: float = 0.0

    # Moyennes mobiles (EMA, SMA, Ichimoku…)
    moving_averages: float = 0.0

    # Indicateurs individuels normalisés
    tv_rsi: float = 0.0
    tv_macd: float = 0.0
    tv_stoch: float = 0.0
    tv_adx: float = 0.0
    tv_bb: float = 0.0
    tv_volume: float = 0.0
    tv_composite: float = 0.0          # Moyenne pondérée de tout

    # Meta
    buy_count: int = 0
    sell_count: int = 0
    neutral_count: int = 0
    timestamp: float = 0.0
    fresh: bool = False

    @property
    def age_sec(self) -> float:
        return time.time() - self.timestamp

    @property
    def is_stale(self) -> bool:
        return self.age_sec > TV_POLL_SEC * 3


# ── Map recommandation texte → valeur ─────────────────────────────────────────

_RECO_MAP = {
    "STRONG_BUY": 1.0,
    "BUY": 0.5,
    "NEUTRAL": 0.0,
    "SELL": -0.5,
    "STRONG_SELL": -1.0,
}

_INDICATOR_MAP = {
    # RSI
    "RSI": lambda v: _normalize_oscillator(v, 30, 70),
    "RSI[1]": lambda v: _normalize_oscillator(v, 30, 70),
    # MACD
    "MACD.macd": lambda v: _sign_norm(v),
    "MACD.signal": lambda v: _sign_norm(v),
    # Stochastic
    "Stoch.K": lambda v: _normalize_oscillator(v, 20, 80),
    "Stoch.D": lambda v: _normalize_oscillator(v, 20, 80),
    "Stoch.K[1]": lambda v: _normalize_oscillator(v, 20, 80),
    # CCI
    "CCI20": lambda v: max(-1.0, min(1.0, v / 200.0)),
    # Williams %R
    "W.R": lambda v: max(-1.0, min(1.0, (-v - 50.0) / 50.0)),
    # ADX
    "ADX": lambda v: max(0.0, min(1.0, (v - 20.0) / 30.0)),
    "ADX+DI": lambda v: max(-1.0, min(1.0, v / 40.0)),
    "ADX-DI": lambda v: max(-1.0, min(1.0, -v / 40.0)),
    # Bollinger
    "BB.upper": lambda v: 0.0,   # comparaison avec price, pas dispo ici
    # MOM
    "Mom": lambda v: _sign_norm(v),
    # MACD histogram
    "MACD.macd": lambda v: _sign_norm(v),
}


def _normalize_oscillator(val: float, low: float, high: float) -> float:
    """Oscillateur : <low = +1 (oversold/bull), >high = -1 (overbought/bear)."""
    if val < low:
        return 1.0 - (val / low) * 0.3
    if val > high:
        return -((val - high) / (100 - high)) * 0.7 - 0.3
    return (50.0 - val) / 50.0 * 0.3


def _sign_norm(val: float) -> float:
    if val > 0:
        return min(1.0, val)
    elif val < 0:
        return max(-1.0, val)
    return 0.0


def _reco_to_float(reco_text: str) -> float:
    return _RECO_MAP.get(reco_text.upper(), 0.0)


# ── Client TradingView ────────────────────────────────────────────────────────

class TradingViewSignals:
    """
    Récupère et met à jour les signaux TradingView pour BTCUSDT 5M.
    """

    def __init__(self) -> None:
        self._latest = TVSignals()
        self._running = False
        self._handler: Optional[object] = None
        if TV_AVAILABLE:
            try:
                self._handler = TA_Handler(
                    symbol=TV_SYMBOL,
                    screener=TV_SCREENER,
                    exchange=TV_EXCHANGE,
                    interval=Interval.INTERVAL_5_MINUTES,
                )
            except Exception as e:
                logger.warning(f"TradingView TA_Handler init: {e}")

    def get_latest(self) -> TVSignals:
        return self._latest

    def is_fresh(self) -> bool:
        return not self._latest.is_stale and self._latest.fresh

    # ── Boucle de polling ─────────────────────────────────────────────────────

    async def run_forever(self) -> None:
        self._running = True
        logger.info(
            f"TradingView Signals démarré "
            f"({'actif' if TV_AVAILABLE else 'désactivé — tradingview-ta manquant'})"
        )
        if not TV_AVAILABLE:
            return

        await self._fetch()  # Premier fetch immédiat
        while self._running:
            await asyncio.sleep(TV_POLL_SEC)
            await self._fetch()

    def stop(self) -> None:
        self._running = False

    # ── Fetch ─────────────────────────────────────────────────────────────────

    async def _fetch(self) -> None:
        if not TV_AVAILABLE or not self._handler:
            return
        try:
            analysis = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, self._handler.get_analysis
                ),
                timeout=TV_TIMEOUT_SEC,
            )
            self._latest = self._parse(analysis)
        except asyncio.TimeoutError:
            logger.debug("TradingView: timeout")
        except Exception as e:
            logger.debug(f"TradingView fetch erreur: {e}")

    def _parse(self, analysis) -> TVSignals:
        sig = TVSignals()
        sig.timestamp = time.time()
        sig.fresh = True

        summary = analysis.summary
        oscillators_data = analysis.oscillators
        moving_avgs = analysis.moving_averages
        indicators = analysis.indicators or {}

        # Recommandation globale
        sig.recommendation = _reco_to_float(summary.get("RECOMMENDATION", "NEUTRAL"))

        # Oscillateurs
        sig.oscillators = _reco_to_float(oscillators_data.get("RECOMMENDATION", "NEUTRAL"))
        sig.buy_count = summary.get("BUY", 0)
        sig.sell_count = summary.get("SELL", 0)
        sig.neutral_count = summary.get("NEUTRAL", 0)

        # Moving averages
        sig.moving_averages = _reco_to_float(moving_avgs.get("RECOMMENDATION", "NEUTRAL"))

        # Indicateurs individuels
        rsi_val = indicators.get("RSI", 50.0) or 50.0
        sig.tv_rsi = _normalize_oscillator(float(rsi_val), 30, 70)

        macd_val = indicators.get("MACD.macd", 0.0) or 0.0
        macd_sig = indicators.get("MACD.signal", 0.0) or 0.0
        sig.tv_macd = min(1.0, max(-1.0, float(macd_val) - float(macd_sig)))

        stoch_k = indicators.get("Stoch.K", 50.0) or 50.0
        sig.tv_stoch = _normalize_oscillator(float(stoch_k), 20, 80)

        adx_val = indicators.get("ADX", 0.0) or 0.0
        di_p = indicators.get("ADX+DI", 0.0) or 0.0
        di_m = indicators.get("ADX-DI", 0.0) or 0.0
        sig.tv_adx = min(1.0, max(-1.0, (float(di_p) - float(di_m)) / (float(adx_val) + 1e-8)))

        # BB position (calculé depuis upper/lower si dispo)
        bb_upper = indicators.get("BB.upper", 0.0) or 0.0
        bb_lower = indicators.get("BB.lower", 0.0) or 0.0
        close = indicators.get("close", 0.0) or 0.0
        if bb_upper and bb_lower and close and bb_upper != bb_lower:
            bb_mid = (bb_upper + bb_lower) / 2
            sig.tv_bb = max(-1.0, min(1.0, (bb_mid - close) / ((bb_upper - bb_lower) / 2)))
        else:
            sig.tv_bb = 0.0

        # Volume signal (via CMF ou MFI si dispo)
        mfi = indicators.get("Money Flow", 50.0) or 50.0
        sig.tv_volume = _normalize_oscillator(float(mfi), 20, 80)

        # Composite pondéré
        components = [
            (sig.recommendation, 2.0),
            (sig.oscillators, 1.5),
            (sig.moving_averages, 1.5),
            (sig.tv_rsi, 1.0),
            (sig.tv_macd, 1.0),
        ]
        total_w = sum(w for _, w in components)
        sig.tv_composite = sum(v * w for v, w in components) / total_w

        logger.debug(
            f"TV: {summary.get('RECOMMENDATION', 'N/A')} "
            f"B={sig.buy_count} S={sig.sell_count} N={sig.neutral_count} "
            f"composite={sig.tv_composite:+.3f}"
        )
        return sig
