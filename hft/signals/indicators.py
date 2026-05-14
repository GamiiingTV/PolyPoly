"""
HFT Indicateurs Techniques — Implémentation NumPy pure (zéro dépendance TA-lib).

Tous les calculs sont vectorisés pour s'exécuter en <1ms sur 100 bougies.
Chaque indicateur retourne sa valeur normalisée en [-1, +1] pour le force-graph.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import numpy as np


# ── Résultat d'un calcul d'indicateurs ────────────────────────────────────────

@dataclass
class IndicatorSet:
    """
    Valeurs brutes + signaux normalisés [-1, +1] de tous les indicateurs.
    Convention signal : +1 = fortement haussier, -1 = fortement baissier.
    """
    # Prix
    close: float = 0.0
    open_: float = 0.0

    # EMAs
    ema9: float = 0.0
    ema21: float = 0.0
    ema50: float = 0.0

    # Bollinger Bands
    bb_upper: float = 0.0
    bb_middle: float = 0.0
    bb_lower: float = 0.0
    bb_width: float = 0.0

    # RSI
    rsi_14: float = 50.0
    rsi_7: float = 50.0

    # MACD
    macd_line: float = 0.0
    macd_signal: float = 0.0
    macd_hist: float = 0.0
    macd_hist_prev: float = 0.0

    # Stochastic
    stoch_k: float = 50.0
    stoch_d: float = 50.0

    # ATR
    atr: float = 0.0
    atr_ratio: float = 1.0       # ATR / MA(ATR)

    # OBV
    obv_slope: float = 0.0       # pente OBV sur 5 bougies

    # CMF
    cmf: float = 0.0

    # Williams %R
    williams_r: float = -50.0

    # CCI
    cci: float = 0.0

    # ROC
    roc_5: float = 0.0
    roc_15: float = 0.0

    # Momentum
    momentum_14: float = 0.0

    # ADX / DI
    adx: float = 0.0
    di_plus: float = 0.0
    di_minus: float = 0.0

    # TRIX
    trix: float = 0.0

    # VWAP (approximé sur les bougies disponibles)
    vwap: float = 0.0

    # Patterns price action
    candle_body_dir: float = 0.0     # +1 verte, -1 rouge
    trend_3: float = 0.0             # moyenne directionnelle 3 bougies
    trend_5: float = 0.0             # moyenne directionnelle 5 bougies
    higher_highs: float = 0.0        # pattern HH (+1) / LL (-1)
    higher_lows: float = 0.0         # pattern HL (+1) / LH (-1)


# ── Helpers NumPy ─────────────────────────────────────────────────────────────

def _ema(arr: np.ndarray, period: int) -> np.ndarray:
    """EMA vectorisée. Retourne tableau de même taille que arr."""
    if len(arr) < period:
        return np.full_like(arr, arr[-1] if len(arr) else 0.0)
    k = 2.0 / (period + 1)
    result = np.empty_like(arr)
    result[0] = arr[0]
    for i in range(1, len(arr)):
        result[i] = arr[i] * k + result[i - 1] * (1 - k)
    return result


def _rsi(closes: np.ndarray, period: int = 14) -> float:
    """RSI de la dernière valeur uniquement."""
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes[-(period + 2):])
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = np.mean(gains[1:])
    avg_loss = np.mean(losses[1:])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _normalize_rsi(rsi: float) -> float:
    """RSI → signal [-1, +1]. <30 = bull, >70 = bear."""
    if rsi < 30:
        return 1.0 - (rsi / 30.0) * 0.3    # [0.7, 1.0]
    if rsi > 70:
        return -((rsi - 70.0) / 30.0) * 0.7 - 0.3   # [-1.0, -0.3]
    # Zone neutre : linéaire de -0.3 à +0.3
    return (50.0 - rsi) / 50.0 * 0.3


def _normalize_linear(val: float, low: float, high: float) -> float:
    """Normalise val ∈ [low, high] → [-1, +1]."""
    mid = (low + high) / 2
    half = (high - low) / 2
    if half == 0:
        return 0.0
    return max(-1.0, min(1.0, (val - mid) / half))


def _stdev(arr: np.ndarray) -> float:
    return float(np.std(arr)) if len(arr) > 1 else 0.0


# ── Moteur de calcul ──────────────────────────────────────────────────────────

class IndicatorEngine:
    """Calcule tous les indicateurs sur les bougies 5M Binance."""

    def compute(
        self,
        opens: list[float],
        highs: list[float],
        lows: list[float],
        closes: list[float],
        volumes: list[float],
        taker_buy_ratios: Optional[list[float]] = None,
    ) -> IndicatorSet:
        """
        Calcule l'ensemble des indicateurs.
        Retourne un IndicatorSet avec valeurs brutes et normalisées.
        """
        ind = IndicatorSet()
        n = len(closes)
        if n < 5:
            return ind

        c = np.array(closes, dtype=np.float64)
        h = np.array(highs, dtype=np.float64)
        l = np.array(lows, dtype=np.float64)
        o = np.array(opens, dtype=np.float64)
        v = np.array(volumes, dtype=np.float64)

        ind.close = c[-1]
        ind.open_ = o[-1]

        # ── EMAs ──────────────────────────────────────────────────────────────
        ema9_arr = _ema(c, 9)
        ema21_arr = _ema(c, 21)
        ema50_arr = _ema(c, 50)
        ind.ema9 = ema9_arr[-1]
        ind.ema21 = ema21_arr[-1]
        ind.ema50 = ema50_arr[-1]

        # ── Bollinger Bands (20, 2) ───────────────────────────────────────────
        if n >= 20:
            window = c[-20:]
            ind.bb_middle = float(np.mean(window))
            std = float(np.std(window))
            ind.bb_upper = ind.bb_middle + 2 * std
            ind.bb_lower = ind.bb_middle - 2 * std
            ind.bb_width = (ind.bb_upper - ind.bb_lower) / ind.bb_middle if ind.bb_middle else 0

        # ── RSI ───────────────────────────────────────────────────────────────
        ind.rsi_14 = _rsi(c, 14)
        ind.rsi_7 = _rsi(c, 7)

        # ── MACD (12, 26, 9) ──────────────────────────────────────────────────
        if n >= 26:
            ema12 = _ema(c, 12)
            ema26 = _ema(c, 26)
            macd_line_arr = ema12 - ema26
            signal_arr = _ema(macd_line_arr, 9)
            hist_arr = macd_line_arr - signal_arr
            ind.macd_line = float(macd_line_arr[-1])
            ind.macd_signal = float(signal_arr[-1])
            ind.macd_hist = float(hist_arr[-1])
            ind.macd_hist_prev = float(hist_arr[-2]) if len(hist_arr) >= 2 else 0.0

        # ── Stochastic (14, 3) ────────────────────────────────────────────────
        if n >= 14:
            window_h = h[-14:]
            window_l = l[-14:]
            hh, ll = float(np.max(window_h)), float(np.min(window_l))
            if hh != ll:
                ind.stoch_k = 100.0 * (c[-1] - ll) / (hh - ll)
            else:
                ind.stoch_k = 50.0
            # %D = moyenne 3 derniers %K
            k_vals = []
            for i in range(3):
                idx = -(i + 1)
                if abs(idx) > n:
                    break
                wh = float(np.max(h[max(-14 + idx, -n):idx] if idx != 0 else h[-14:]))
                wl = float(np.min(l[max(-14 + idx, -n):idx] if idx != 0 else l[-14:]))
                if wh != wl:
                    k_vals.append(100.0 * (c[idx] - wl) / (wh - wl))
                else:
                    k_vals.append(50.0)
            ind.stoch_d = float(np.mean(k_vals)) if k_vals else ind.stoch_k

        # ── ATR (14) ─────────────────────────────────────────────────────────
        if n >= 14:
            tr = np.maximum(h[1:] - l[1:],
                 np.maximum(np.abs(h[1:] - c[:-1]),
                            np.abs(l[1:] - c[:-1])))
            atr_arr = _ema(tr, 14)
            ind.atr = float(atr_arr[-1])
            if len(atr_arr) >= 14:
                ind.atr_ratio = ind.atr / (float(np.mean(atr_arr[-14:])) + 1e-8)

        # ── OBV (pente) ───────────────────────────────────────────────────────
        if n >= 6:
            obv = np.zeros(n)
            for i in range(1, n):
                if c[i] > c[i - 1]:
                    obv[i] = obv[i - 1] + v[i]
                elif c[i] < c[i - 1]:
                    obv[i] = obv[i - 1] - v[i]
                else:
                    obv[i] = obv[i - 1]
            obv_recent = obv[-5:]
            if obv_recent[-1] != obv_recent[0]:
                ind.obv_slope = (obv_recent[-1] - obv_recent[0]) / (abs(obv_recent[0]) + 1e-8)

        # ── CMF (Chaikin Money Flow, 20) ──────────────────────────────────────
        if n >= 20:
            rng = h[-20:] - l[-20:]
            rng = np.where(rng == 0, 1e-8, rng)
            mfm = ((c[-20:] - l[-20:]) - (h[-20:] - c[-20:])) / rng
            mfv = mfm * v[-20:]
            ind.cmf = float(np.sum(mfv) / (np.sum(v[-20:]) + 1e-8))

        # ── Williams %R (14) ─────────────────────────────────────────────────
        if n >= 14:
            hh = float(np.max(h[-14:]))
            ll = float(np.min(l[-14:]))
            if hh != ll:
                ind.williams_r = -100.0 * (hh - c[-1]) / (hh - ll)
            else:
                ind.williams_r = -50.0

        # ── CCI (20) ─────────────────────────────────────────────────────────
        if n >= 20:
            tp = (h[-20:] + l[-20:] + c[-20:]) / 3.0
            tp_mean = float(np.mean(tp))
            mean_dev = float(np.mean(np.abs(tp - tp_mean)))
            if mean_dev > 0:
                ind.cci = (tp[-1] - tp_mean) / (0.015 * mean_dev)

        # ── ROC ──────────────────────────────────────────────────────────────
        if n >= 6:
            ind.roc_5 = (c[-1] / c[-6] - 1.0) * 100.0 if c[-6] != 0 else 0.0
        if n >= 16:
            ind.roc_15 = (c[-1] / c[-16] - 1.0) * 100.0 if c[-16] != 0 else 0.0

        # ── Momentum (14) ────────────────────────────────────────────────────
        if n >= 15:
            ind.momentum_14 = c[-1] - c[-15]

        # ── ADX / DI+ / DI- (14) ─────────────────────────────────────────────
        if n >= 20:
            up_moves = h[1:] - h[:-1]
            down_moves = l[:-1] - l[1:]
            dm_plus = np.where((up_moves > down_moves) & (up_moves > 0), up_moves, 0.0)
            dm_minus = np.where((down_moves > up_moves) & (down_moves > 0), down_moves, 0.0)
            tr = np.maximum(h[1:] - l[1:],
                 np.maximum(np.abs(h[1:] - c[:-1]),
                            np.abs(l[1:] - c[:-1])))
            atr14 = float(np.mean(tr[-14:]))
            di_p = 100.0 * float(np.mean(dm_plus[-14:])) / (atr14 + 1e-8)
            di_m = 100.0 * float(np.mean(dm_minus[-14:])) / (atr14 + 1e-8)
            ind.di_plus = di_p
            ind.di_minus = di_m
            dx = abs(di_p - di_m) / (di_p + di_m + 1e-8) * 100
            ind.adx = float(np.mean([dx]))

        # ── TRIX (18 periods) ─────────────────────────────────────────────────
        if n >= 54:
            ema1 = _ema(c, 18)
            ema2 = _ema(ema1, 18)
            ema3 = _ema(ema2, 18)
            if ema3[-2] != 0:
                ind.trix = (ema3[-1] - ema3[-2]) / ema3[-2] * 100

        # ── VWAP (approximé sur toute la période disponible) ─────────────────
        if n >= 1:
            tp = (h + l + c) / 3.0
            cum_v = np.cumsum(v)
            cum_vp = np.cumsum(tp * v)
            ind.vwap = float(cum_vp[-1] / (cum_v[-1] + 1e-8))

        # ── Patterns price action ─────────────────────────────────────────────
        ind.candle_body_dir = (
            1.0 if c[-1] > o[-1] else (-1.0 if c[-1] < o[-1] else 0.0)
        )
        if n >= 3:
            dirs_3 = [1.0 if c[i] > o[i] else -1.0 for i in range(-3, 0)]
            ind.trend_3 = float(np.mean(dirs_3))
        if n >= 5:
            dirs_5 = [1.0 if c[i] > o[i] else -1.0 for i in range(-5, 0)]
            ind.trend_5 = float(np.mean(dirs_5))

        # Higher Highs / Higher Lows
        if n >= 4:
            hh_pattern = (h[-1] > h[-2] and h[-2] > h[-3])
            ll_pattern = (l[-1] < l[-2] and l[-2] < l[-3])
            hl_pattern = (l[-1] > l[-2])
            lh_pattern = (h[-1] < h[-2])
            if hh_pattern:
                ind.higher_highs = 1.0
            elif ll_pattern:
                ind.higher_highs = -1.0
            if hl_pattern:
                ind.higher_lows = 1.0
            elif lh_pattern:
                ind.higher_lows = -1.0

        return ind

    # ── Normaliseurs pour le force-graph ─────────────────────────────────────

    @staticmethod
    def normalize(ind: IndicatorSet) -> dict[str, float]:
        """
        Retourne un dict de signaux normalisés [-1, +1] pour chaque indicateur.
        +1 = fortement haussier, -1 = fortement baissier.
        """
        close = ind.close or 1.0

        signals: dict[str, float] = {}

        # ── Trend direction (alignement EMA) ─────────────────────────────────
        ema_bull = int(ind.ema9 > ind.ema21) + int(ind.ema21 > ind.ema50)
        signals["trend_direction"] = (ema_bull - 1) / 1.0    # -1, 0, +1

        # ── EMAs vs price ─────────────────────────────────────────────────────
        signals["ema9_vs_price"] = max(-1.0, min(1.0, (close - ind.ema9) / (close * 0.01)))
        signals["ema21_vs_price"] = max(-1.0, min(1.0, (close - ind.ema21) / (close * 0.01)))
        signals["ema50_vs_price"] = max(-1.0, min(1.0, (close - ind.ema50) / (close * 0.02)))

        # ── EMA crosses ───────────────────────────────────────────────────────
        signals["ema9_vs_ema21"] = math.copysign(1.0, ind.ema9 - ind.ema21) if ind.ema9 != ind.ema21 else 0.0
        signals["ema21_vs_ema50"] = math.copysign(1.0, ind.ema21 - ind.ema50) if ind.ema21 != ind.ema50 else 0.0

        # ── Bollinger Bands ───────────────────────────────────────────────────
        bb_range = ind.bb_upper - ind.bb_lower if ind.bb_upper != ind.bb_lower else 1.0
        if ind.bb_middle:
            signals["price_vs_bb_middle"] = max(-1.0, min(1.0, (close - ind.bb_middle) / (bb_range / 2)))
            # Trop proche du haut = baissier (overbought)
            signals["price_vs_bb_upper"] = max(-1.0, min(1.0, -(close - ind.bb_middle) / (bb_range / 2)))
            # Proche du bas = haussier (oversold)
            signals["price_vs_bb_lower"] = max(-1.0, min(1.0, (ind.bb_middle - close) / (bb_range / 2)))
        else:
            signals["price_vs_bb_middle"] = 0.0
            signals["price_vs_bb_upper"] = 0.0
            signals["price_vs_bb_lower"] = 0.0

        # ── Candles ───────────────────────────────────────────────────────────
        signals["candle_direction"] = ind.candle_body_dir
        signals["candle_trend_3"] = max(-1.0, min(1.0, ind.trend_3))
        signals["candle_trend_5"] = max(-1.0, min(1.0, ind.trend_5))

        # ── Momentum price ────────────────────────────────────────────────────
        signals["price_momentum_short"] = max(-1.0, min(1.0, ind.roc_5 / 2.0))
        signals["price_momentum_medium"] = max(-1.0, min(1.0, ind.roc_15 / 3.0))

        # ── Higher Highs / Lows ───────────────────────────────────────────────
        signals["higher_highs"] = ind.higher_highs
        signals["higher_lows"] = ind.higher_lows

        # ── VWAP ─────────────────────────────────────────────────────────────
        signals["vwap_vs_price"] = max(-1.0, min(1.0, (close - ind.vwap) / (close * 0.01))) if ind.vwap else 0.0

        # ── Price acceleration ────────────────────────────────────────────────
        signals["price_acceleration"] = max(-1.0, min(1.0, ind.momentum_14 / (close * 0.02))) if close else 0.0

        # ── Volume ────────────────────────────────────────────────────────────
        signals["volume_ratio"] = max(-1.0, min(1.0, ind.obv_slope * 10.0))
        signals["volume_trend"] = math.copysign(1.0, ind.obv_slope) if ind.obv_slope != 0 else 0.0
        signals["obv_trend"] = max(-1.0, min(1.0, ind.obv_slope * 5.0))
        signals["cmf"] = max(-1.0, min(1.0, ind.cmf * 3.0))

        # ── RSI ───────────────────────────────────────────────────────────────
        signals["rsi_14"] = _normalize_rsi(ind.rsi_14)
        signals["rsi_7"] = _normalize_rsi(ind.rsi_7)
        signals["rsi_direction"] = math.copysign(1.0, ind.rsi_14 - ind.rsi_7) if ind.rsi_14 != ind.rsi_7 else 0.0

        # ── MACD ─────────────────────────────────────────────────────────────
        signals["macd_line"] = max(-1.0, min(1.0, ind.macd_line / (close * 0.003) if close else 0.0))
        signals["macd_histogram"] = max(-1.0, min(1.0, ind.macd_hist / (close * 0.001) if close else 0.0))
        hist_dir = ind.macd_hist - ind.macd_hist_prev
        signals["macd_histogram_dir"] = math.copysign(1.0, hist_dir) if hist_dir != 0 else 0.0

        # ── Stochastic ────────────────────────────────────────────────────────
        signals["stoch_k_vs_d"] = max(-1.0, min(1.0, (ind.stoch_k - ind.stoch_d) / 20.0))
        # <20 = haussier, >80 = baissier
        if ind.stoch_k < 20:
            signals["stoch_level"] = 1.0
        elif ind.stoch_k > 80:
            signals["stoch_level"] = -1.0
        else:
            signals["stoch_level"] = (50.0 - ind.stoch_k) / 50.0 * 0.5

        # ── Williams %R ───────────────────────────────────────────────────────
        # <-80 = haussier, >-20 = baissier
        signals["williams_r"] = max(-1.0, min(1.0, (-ind.williams_r - 50.0) / 50.0))

        # ── CCI ───────────────────────────────────────────────────────────────
        # >100 = haussier (momentum), <-100 = baissier
        signals["cci"] = max(-1.0, min(1.0, ind.cci / 200.0))

        # ── ROC ───────────────────────────────────────────────────────────────
        signals["roc_5"] = max(-1.0, min(1.0, ind.roc_5 / 2.0))
        signals["roc_15"] = max(-1.0, min(1.0, ind.roc_15 / 3.0))

        # ── Momentum ─────────────────────────────────────────────────────────
        signals["momentum_14"] = max(-1.0, min(1.0, ind.momentum_14 / (close * 0.02) if close else 0.0))

        # ── TRIX ─────────────────────────────────────────────────────────────
        signals["trix"] = max(-1.0, min(1.0, ind.trix * 10.0))

        # ── ADX / DI ─────────────────────────────────────────────────────────
        dmi_diff = ind.di_plus - ind.di_minus
        signals["dmi_direction"] = max(-1.0, min(1.0, dmi_diff / 20.0))
        # ADX >25 = tendance forte (amplificateur, pas directionnel)
        signals["adx_strength"] = max(-1.0, min(1.0, (ind.adx - 20.0) / 30.0))

        # ── Volatility signals ────────────────────────────────────────────────
        # BB width normalisée : plus c'est large, plus la vol est élevée
        signals["bb_width"] = max(-1.0, min(1.0, ind.bb_width / 0.04 - 1.0)) if ind.bb_width else 0.0
        # ATR ratio > 1 = volatilité croissante
        signals["atr_ratio"] = max(-1.0, min(1.0, (ind.atr_ratio - 1.0) * 2.0))

        # ── Market structure ──────────────────────────────────────────────────
        # Trend strength = combinaison ADX + alignement EMA
        trend_components = [
            signals["trend_direction"],
            signals["ema9_vs_ema21"],
            signals["ema21_vs_ema50"],
            min(1.0, ind.adx / 30.0) * signals.get("dmi_direction", 0),
        ]
        signals["trend_strength"] = float(np.mean(trend_components))

        return signals
