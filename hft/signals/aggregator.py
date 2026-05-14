"""
HFT Signal Aggregator — Injecte tous les signaux dans le force-graph.

Rôle : transformer les données brutes de chaque feed en valeurs [-1, +1]
et les distribuer aux 100 nœuds du force-graph avant chaque calcul.
"""

from __future__ import annotations

import time
from typing import Optional

from loguru import logger

from hft.signals.force_graph import ForceGraph
from hft.signals.indicators import IndicatorSet, IndicatorEngine
from hft.signals.tradingview_signals import TVSignals
from hft.feeds.cryptoquant_feed import ExchangeFlowData
from hft.feeds.polymarket_clob_feed import BTCMarket


class SignalAggregator:
    """
    Agrège tous les signaux disponibles dans le force-graph.

    Appelé à chaque tick Binance ou à chaque événement de marché.
    Conçu pour s'exécuter en <2ms (tout en mémoire, pas d'I/O).
    """

    def __init__(self) -> None:
        self._engine = IndicatorEngine()
        self._last_update: float = 0.0

    def update(
        self,
        graph: ForceGraph,
        ind: IndicatorSet,
        ind_signals: dict[str, float],
        tv: TVSignals,
        cq: ExchangeFlowData,
        market: Optional[BTCMarket],
        spot_price: float,
        poly_yes_price: float,
        estimated_true_prob: float,
    ) -> None:
        """
        Injecte toutes les données dans le force-graph.

        Args:
            graph:               instance ForceGraph à mettre à jour
            ind:                 IndicatorSet brut
            ind_signals:         signaux normalisés de IndicatorEngine.normalize()
            tv:                  signaux TradingView
            cq:                  données CryptoQuant / dérivés
            market:              marché Polymarket actif (ou None)
            spot_price:          prix BTC spot Binance
            poly_yes_price:      prix YES actuel Polymarket
            estimated_true_prob: probabilité estimée par notre modèle
        """
        # ── Groupe A : Price Action ───────────────────────────────────────────
        graph.set_by_name("trend_direction",      ind_signals.get("trend_direction", 0))
        graph.set_by_name("ema9_vs_price",         ind_signals.get("ema9_vs_price", 0))
        graph.set_by_name("ema21_vs_price",        ind_signals.get("ema21_vs_price", 0))
        graph.set_by_name("ema50_vs_price",        ind_signals.get("ema50_vs_price", 0))
        graph.set_by_name("ema9_vs_ema21",         ind_signals.get("ema9_vs_ema21", 0))
        graph.set_by_name("ema21_vs_ema50",        ind_signals.get("ema21_vs_ema50", 0))
        graph.set_by_name("price_vs_bb_middle",    ind_signals.get("price_vs_bb_middle", 0))
        graph.set_by_name("price_vs_bb_upper",     ind_signals.get("price_vs_bb_upper", 0))
        graph.set_by_name("price_vs_bb_lower",     ind_signals.get("price_vs_bb_lower", 0))
        graph.set_by_name("candle_direction",      ind_signals.get("candle_direction", 0))
        graph.set_by_name("candle_trend_3",        ind_signals.get("candle_trend_3", 0))
        graph.set_by_name("candle_trend_5",        ind_signals.get("candle_trend_5", 0))
        graph.set_by_name("price_momentum_short",  ind_signals.get("price_momentum_short", 0))
        graph.set_by_name("price_momentum_medium", ind_signals.get("price_momentum_medium", 0))
        graph.set_by_name("higher_highs",          ind_signals.get("higher_highs", 0))
        graph.set_by_name("higher_lows",           ind_signals.get("higher_lows", 0))
        graph.set_by_name("vwap_vs_price",         ind_signals.get("vwap_vs_price", 0))
        graph.set_by_name("price_acceleration",    ind_signals.get("price_acceleration", 0))

        # Support / Résistance (approximé depuis BB + swing highs/lows)
        bb_pos = ind_signals.get("price_vs_bb_lower", 0)
        graph.set_by_name("support_proximity",    max(0.0, bb_pos))
        graph.set_by_name("resistance_proximity", max(0.0, -ind_signals.get("price_vs_bb_upper", 0)))

        # ── Groupe B : Volume / Flow ──────────────────────────────────────────
        graph.set_by_name("volume_ratio",     ind_signals.get("volume_ratio", 0))
        graph.set_by_name("volume_trend",     ind_signals.get("volume_trend", 0))
        graph.set_by_name("buy_vol_dominance", 0.0)   # sera rempli si taker_buy_ratio dispo
        graph.set_by_name("obv_trend",        ind_signals.get("obv_trend", 0))
        graph.set_by_name("cmf",              ind_signals.get("cmf", 0))

        # CryptoQuant flows
        if not cq.stale:
            graph.set_by_name("exchange_inflow",  cq.inflow_signal)
            graph.set_by_name("exchange_outflow", cq.outflow_signal)
            graph.set_by_name("net_flow",         cq.net_position_change)
            graph.set_by_name("funding_rate",     -cq.funding_rate * 0.5)  # funding élevé = bear
            # Long/short ratio contrarian : trop de longs → signal baissier
            ls_signal = max(-1.0, min(1.0, (1.0 - cq.long_short_ratio) * 0.5))
            graph.set_by_name("long_short_ratio", ls_signal)
        else:
            graph.set_by_name("exchange_inflow",  0.0)
            graph.set_by_name("exchange_outflow", 0.0)
            graph.set_by_name("net_flow",         0.0)
            graph.set_by_name("funding_rate",     0.0)
            graph.set_by_name("long_short_ratio", 0.0)

        graph.set_by_name("whale_activity",  0.0)   # rempli par CLOB si dispo
        graph.set_by_name("oi_change",       max(-1.0, min(1.0, cq.open_interest_change_pct / 5.0)) if not cq.stale else 0.0)
        graph.set_by_name("spot_perp_premium", 0.0)  # à câbler avec futures feed
        graph.set_by_name("volume_breakout",   ind_signals.get("volume_ratio", 0))
        graph.set_by_name("taker_buy_ratio",   ind_signals.get("volume_ratio", 0))

        # ── Groupe C : Momentum ───────────────────────────────────────────────
        graph.set_by_name("rsi_14",           ind_signals.get("rsi_14", 0))
        graph.set_by_name("rsi_7",            ind_signals.get("rsi_7", 0))
        graph.set_by_name("rsi_direction",    ind_signals.get("rsi_direction", 0))
        graph.set_by_name("rsi_divergence",   0.0)   # divergence nécessite historique RSI
        graph.set_by_name("macd_line",        ind_signals.get("macd_line", 0))
        graph.set_by_name("macd_histogram",   ind_signals.get("macd_histogram", 0))
        graph.set_by_name("macd_histogram_dir", ind_signals.get("macd_histogram_dir", 0))
        graph.set_by_name("stoch_k_vs_d",     ind_signals.get("stoch_k_vs_d", 0))
        graph.set_by_name("stoch_level",      ind_signals.get("stoch_level", 0))
        graph.set_by_name("williams_r",       ind_signals.get("williams_r", 0))
        graph.set_by_name("cci",              ind_signals.get("cci", 0))
        graph.set_by_name("mfi",              ind_signals.get("cmf", 0))   # CMF comme proxy MFI
        graph.set_by_name("roc_5",            ind_signals.get("roc_5", 0))
        graph.set_by_name("roc_15",           ind_signals.get("roc_15", 0))
        graph.set_by_name("momentum_14",      ind_signals.get("momentum_14", 0))
        graph.set_by_name("trix",             ind_signals.get("trix", 0))
        graph.set_by_name("dmi_direction",    ind_signals.get("dmi_direction", 0))
        graph.set_by_name("adx_strength",     ind_signals.get("adx_strength", 0))
        graph.set_by_name("aroon_oscillator", 0.0)
        graph.set_by_name("ultimate_oscillator", 0.0)

        # ── Groupe D : Volatilité ─────────────────────────────────────────────
        graph.set_by_name("bb_width",     ind_signals.get("bb_width", 0))
        graph.set_by_name("bb_squeeze",   -abs(ind_signals.get("bb_width", 0)))  # squeeze = bb_width faible
        graph.set_by_name("atr_ratio",    ind_signals.get("atr_ratio", 0))
        graph.set_by_name("volatility_regime",   0.0)
        graph.set_by_name("keltner_position",    0.0)
        graph.set_by_name("stddev_norm",         0.0)
        graph.set_by_name("chaikin_volatility",  0.0)
        graph.set_by_name("hist_vol_trend",      0.0)
        graph.set_by_name("realized_vol",        0.0)
        graph.set_by_name("vol_trend_signal",    0.0)

        # ── Groupe E : Structure ──────────────────────────────────────────────
        graph.set_by_name("trend_strength",     ind_signals.get("trend_strength", 0))
        graph.set_by_name("market_phase",       ind_signals.get("trend_direction", 0))
        graph.set_by_name("swing_high_proximity", -ind_signals.get("resistance_proximity", 0))
        graph.set_by_name("swing_low_proximity",   ind_signals.get("support_proximity", 0))
        graph.set_by_name("fibonacci_level",    0.0)
        graph.set_by_name("round_number",       0.0)
        graph.set_by_name("ichimoku_position",  ind_signals.get("vwap_vs_price", 0))
        graph.set_by_name("ichimoku_tk_cross",  0.0)
        graph.set_by_name("pivot_proximity",    0.0)
        graph.set_by_name("regression_channel", ind_signals.get("trend_strength", 0))

        # ── Groupe F : TradingView ────────────────────────────────────────────
        if tv.fresh and not tv.is_stale:
            graph.set_by_name("tv_recommendation", tv.recommendation)
            graph.set_by_name("tv_oscillators",    tv.oscillators)
            graph.set_by_name("tv_ma_consensus",   tv.moving_averages)
            graph.set_by_name("tv_rsi",            tv.tv_rsi)
            graph.set_by_name("tv_macd",           tv.tv_macd)
            graph.set_by_name("tv_stochastic",     tv.tv_stoch)
            graph.set_by_name("tv_adx",            tv.tv_adx)
            graph.set_by_name("tv_bb",             tv.tv_bb)
            graph.set_by_name("tv_volume",         tv.tv_volume)
            graph.set_by_name("tv_composite",      tv.tv_composite)
        # Sinon on laisse les valeurs précédentes (cache)

        # ── Groupe G : External / Polymarket ─────────────────────────────────
        # Signal clé : notre edge estimé sur Polymarket
        if market is not None and spot_price > 0:
            # Probabilité implicite du marché
            poly_prob = market.yes_price if market.yes_price > 0 else 0.5
            # Notre estimation
            our_prob = estimated_true_prob
            # Edge = différence entre nos deux estimations
            edge = our_prob - poly_prob
            # Normalisé : ±5% d'edge → [-1, +1]
            poly_edge_signal = max(-1.0, min(1.0, edge / 0.05))
            graph.set_by_name("poly_edge", poly_edge_signal)

            # Qualité du spread CLOB (spread faible = signal de qualité)
            spread = market.spread_pct
            spread_quality = max(-1.0, min(1.0, 1.0 - spread / 0.05))
            graph.set_by_name("clob_spread_quality", spread_quality)

            # Profondeur CLOB imbalance
            graph.set_by_name("clob_depth_imbalance", market.depth_imbalance)

            # Flow récent CLOB (approximé depuis direction du trade)
            # Si poly_edge > 0 (on est bull mais poly est bas), clob_trade_flow
            # sera mis à jour par le LagDetector
            if abs(edge) > 0.01:
                graph.set_by_name("clob_trade_flow", edge * 2)
        else:
            graph.set_by_name("poly_edge",           0.0)
            graph.set_by_name("clob_spread_quality", 0.0)
            graph.set_by_name("clob_depth_imbalance", 0.0)
            graph.set_by_name("clob_trade_flow",     0.0)

        # Fear & Greed (neutre si pas de source)
        graph.set_by_name("fear_greed",       0.0)   # à câbler avec API externe
        graph.set_by_name("btc_dominance",    0.0)
        graph.set_by_name("crypto_market_trend", 0.0)
        graph.set_by_name("options_pcr",      0.0)
        graph.set_by_name("liq_level_up",     0.0)
        graph.set_by_name("liq_level_down",   0.0)
        graph.set_by_name("order_flow_toxicity", 0.0)
        graph.set_by_name("time_of_day_bias", _time_of_day_bias())
        graph.set_by_name("news_sentiment",   0.0)
        graph.set_by_name("social_sentiment", 0.0)

        # Signal composite final = moyenne pondérée des groupes
        composite = (
            ind_signals.get("trend_strength", 0) * 0.3
            + ind_signals.get("rsi_14", 0) * 0.2
            + ind_signals.get("macd_histogram", 0) * 0.2
            + (tv.tv_composite if tv.fresh else 0.0) * 0.3
        )
        graph.set_by_name("composite_signal", max(-1.0, min(1.0, composite)))

        self._last_update = time.time()


def _time_of_day_bias() -> float:
    """
    Biais de session horaire en [-1, +1].
    Session US (13h-22h UTC) = légèrement haussier (plus de volume)
    Session Asie (0h-8h UTC) = légèrement baissier (range)
    """
    import datetime
    hour = datetime.datetime.utcnow().hour
    if 13 <= hour < 22:   # Session US
        return 0.2
    elif 7 <= hour < 13:  # Session EU
        return 0.1
    else:                  # Session Asie
        return -0.1
