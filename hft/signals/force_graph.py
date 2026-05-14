"""
HFT Force-Graph — Détecteur de convergence BULL/BEAR.

Architecture :
  • 100 nœuds représentant des dimensions de signal du marché BTC
  • 180 connexions pondérées entre signaux corrélés
  • Propagation itérative par matrice adjacente NumPy (vectorisée)
  • Convergence = |champ pondéré| ≥ seuil (0.65 par défaut)

Principe physique :
  Chaque nœud a une "charge" en [-1, +1] (bull/bear).
  Les arêtes exercent une influence : un voisin bullish tire un nœud vers +1.
  Après N itérations, le champ moyen indique la direction consensuelle.
  Plus le champ est fort, plus la convergence est claire.

Complexité : O(N² dense) → O(E) sparse = O(180) par itération ≈ <0.5ms.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np

from hft.config_hft import (
    FORCE_GRAPH_CONVERGENCE_THRESHOLD,
    FORCE_GRAPH_ITERATIONS,
    FORCE_GRAPH_ALPHA,
)


# ══════════════════════════════════════════════════════════════════════════════
# DÉFINITION DES 100 NŒUDS
# ══════════════════════════════════════════════════════════════════════════════

NODE_NAMES: Final[list[str]] = [
    # ── Groupe A : Price Action (0-19) ────────────────────────────────────────
    "trend_direction",       # 0  alignement EMA9/21/50
    "ema9_vs_price",         # 1  price au-dessus/en-dessous EMA9
    "ema21_vs_price",        # 2  price au-dessus/en-dessous EMA21
    "ema50_vs_price",        # 3  price au-dessus/en-dessous EMA50
    "ema9_vs_ema21",         # 4  croisement court/moyen terme
    "ema21_vs_ema50",        # 5  croisement moyen/long terme
    "price_vs_bb_middle",    # 6  price vs bande médiane Bollinger
    "price_vs_bb_upper",     # 7  proche BB upper = overbought (bear)
    "price_vs_bb_lower",     # 8  proche BB lower = oversold (bull)
    "candle_direction",      # 9  dernière bougie 5M verte/rouge
    "candle_trend_3",        # 10 tendance des 3 dernières bougies
    "candle_trend_5",        # 11 tendance des 5 dernières bougies
    "price_momentum_short",  # 12 momentum court terme (ROC 5)
    "price_momentum_medium", # 13 momentum moyen terme (ROC 15)
    "higher_highs",          # 14 pattern HH (+1) / LL (-1)
    "higher_lows",           # 15 pattern HL (+1) / LH (-1)
    "vwap_vs_price",         # 16 price au-dessus/en-dessous VWAP
    "price_acceleration",    # 17 dérivée seconde de price (momentum accélérant)
    "support_proximity",     # 18 proche support fort (bull)
    "resistance_proximity",  # 19 proche résistance forte (bear)

    # ── Groupe B : Volume / Flow (20-34) ─────────────────────────────────────
    "volume_ratio",          # 20 volume courant vs moyenne 20 bougies
    "volume_trend",          # 21 volume croissant/décroissant
    "buy_vol_dominance",     # 22 volume taker acheteur dominant
    "obv_trend",             # 23 On Balance Volume direction
    "cmf",                   # 24 Chaikin Money Flow
    "exchange_inflow",       # 25 inflow échanges CryptoQuant (inversé : élevé=bear)
    "exchange_outflow",      # 26 outflow échanges (bull)
    "net_flow",              # 27 flux net exchanges
    "whale_activity",        # 28 détection grosses transactions
    "funding_rate",          # 29 funding perp (positif=longs dominent=risk)
    "oi_change",             # 30 variation Open Interest (hausseOI+hausse prix=bull)
    "long_short_ratio",      # 31 ratio L/S (contrarian : trop de longs=bear)
    "spot_perp_premium",     # 32 prime spot vs perp (positif=bull)
    "volume_breakout",       # 33 pic de volume = breakout
    "taker_buy_ratio",       # 34 ratio volume acheteur taker

    # ── Groupe C : Momentum (35-54) ──────────────────────────────────────────
    "rsi_14",                # 35 RSI 14 normalisé
    "rsi_7",                 # 36 RSI 7 (plus réactif)
    "rsi_direction",         # 37 RSI en hausse/baisse
    "rsi_divergence",        # 38 divergence RSI/price
    "macd_line",             # 39 MACD line vs signal
    "macd_histogram",        # 40 MACD histogram (positif=bull)
    "macd_histogram_dir",    # 41 MACD histogram croissant/décroissant
    "stoch_k_vs_d",          # 42 croisement Stochastique K/D
    "stoch_level",           # 43 niveau stochastique (<20=bull, >80=bear)
    "williams_r",            # 44 Williams %R (<-80=bull, >-20=bear)
    "cci",                   # 45 CCI (>100=bull, <-100=bear)
    "mfi",                   # 46 Money Flow Index (comme RSI mais volume)
    "roc_5",                 # 47 Rate of Change 5 périodes
    "roc_15",                # 48 Rate of Change 15 périodes
    "momentum_14",           # 49 Momentum oscillateur 14
    "trix",                  # 50 TRIX (triple EMA lissée)
    "dmi_direction",         # 51 DI+/DI- direction
    "adx_strength",          # 52 ADX > 25 = tendance forte
    "aroon_oscillator",      # 53 Aroon oscillateur
    "ultimate_oscillator",   # 54 Ultimate Oscillator

    # ── Groupe D : Volatilité (55-64) ────────────────────────────────────────
    "bb_width",              # 55 largeur BB (squeeze → breakout imminent)
    "bb_squeeze",            # 56 BB + Keltner squeeze détecté
    "atr_ratio",             # 57 ATR vs sa MA (vol croissante)
    "volatility_regime",     # 58 régime haut/bas volatilité
    "keltner_position",      # 59 position dans canal Keltner
    "stddev_norm",           # 60 écart-type prix normalisé
    "chaikin_volatility",    # 61 variation range sur 10 bougies
    "hist_vol_trend",        # 62 tendance vol historique
    "realized_vol",          # 63 vol réalisée récente
    "vol_trend_signal",      # 64 signal directionnel vol

    # ── Groupe E : Structure de marché (65-74) ────────────────────────────────
    "trend_strength",        # 65 force de tendance composite
    "market_phase",          # 66 phase : accumulation/markup/distribution/markdown
    "swing_high_proximity",  # 67 proche swing high (bear)
    "swing_low_proximity",   # 68 proche swing low (bull)
    "fibonacci_level",       # 69 niveau Fibonacci proche
    "round_number",          # 70 niveau rond proche ($1k BTC)
    "ichimoku_position",     # 71 position vs nuage Ichimoku
    "ichimoku_tk_cross",     # 72 croisement Tenkan/Kijun
    "pivot_proximity",       # 73 proche point pivot daily
    "regression_channel",    # 74 position dans canal de régression

    # ── Groupe F : TradingView (75-84) ───────────────────────────────────────
    "tv_recommendation",     # 75 STRONG_BUY → STRONG_SELL
    "tv_oscillators",        # 76 consensus oscillateurs TV
    "tv_ma_consensus",       # 77 consensus moyennes mobiles TV
    "tv_rsi",                # 78 RSI selon TV
    "tv_macd",               # 79 MACD selon TV
    "tv_stochastic",         # 80 Stochastique selon TV
    "tv_adx",                # 81 ADX/DMI selon TV
    "tv_bb",                 # 82 Bollinger selon TV
    "tv_volume",             # 83 indicateurs volume TV (MFI)
    "tv_composite",          # 84 score composite TV pondéré

    # ── Groupe G : External / Contexte (85-99) ────────────────────────────────
    "poly_edge",             # 85 notre edge estimé sur Polymarket ← signal clé
    "clob_spread_quality",   # 86 spread bid-ask serré = marché liquide (bon)
    "clob_trade_flow",       # 87 direction des trades récents CLOB
    "clob_depth_imbalance",  # 88 déséquilibre profondeur carnet (bid>ask=bull)
    "fear_greed",            # 89 indice peur/avidité normalisé
    "btc_dominance",         # 90 dominance BTC (stable/montante = bull)
    "crypto_market_trend",   # 91 tendance marché crypto global
    "options_pcr",           # 92 Put/Call ratio (contrarian)
    "liq_level_up",          # 93 niveaux liquidation haussiers (au-dessus)
    "liq_level_down",        # 94 niveaux liquidation baissiers (en-dessous)
    "order_flow_toxicity",   # 95 toxicité flux ordres (VPIN proxy)
    "time_of_day_bias",      # 96 biais session (Asia/EU/US)
    "news_sentiment",        # 97 sentiment nouvelles crypto
    "social_sentiment",      # 98 sentiment réseaux sociaux
    "composite_signal",      # 99 signal composite global
]

assert len(NODE_NAMES) == 100, f"Expected 100 nodes, got {len(NODE_NAMES)}"


# ══════════════════════════════════════════════════════════════════════════════
# DÉFINITION DES 180 CONNEXIONS (node_i, node_j, poids)
# ══════════════════════════════════════════════════════════════════════════════
# Poids : 0.0-1.0 (plus fort = influence plus forte entre les deux nœuds)

EDGES: Final[list[tuple[int, int, float]]] = [
    # ── Intra Groupe A : Price Action (15 arêtes) ─────────────────────────────
    (0,  1,  0.85), (0,  2,  0.85), (0,  3,  0.75),
    (1,  4,  0.90), (2,  4,  0.90), (2,  5,  0.90),
    (3,  5,  0.80), (4,  5,  0.70),
    (9,  10, 0.90), (10, 11, 0.90), (9,  11, 0.70),
    (14, 15, 0.90), (12, 13, 0.80),
    (0,  14, 0.80), (0,  15, 0.80),

    # ── Intra Groupe B : Volume/Flow (10 arêtes) ─────────────────────────────
    (20, 21, 0.80), (20, 33, 0.90), (21, 23, 0.80),
    (22, 34, 0.90), (25, 27, 0.80), (26, 27, 0.80),
    (25, 26, 0.70), (29, 30, 0.70), (29, 32, 0.80),
    (30, 31, 0.60),

    # ── Intra Groupe C : Momentum (15 arêtes) ────────────────────────────────
    (35, 36, 0.80), (35, 37, 0.90), (36, 37, 0.80),
    (35, 38, 0.70), (39, 40, 0.90), (40, 41, 0.90),
    (39, 41, 0.80), (42, 43, 0.90), (43, 44, 0.70),
    (35, 43, 0.70), (47, 48, 0.80), (47, 49, 0.90),
    (51, 52, 0.90), (50, 41, 0.70), (53, 51, 0.80),

    # ── Intra Groupe D : Volatilité (6 arêtes) ───────────────────────────────
    (55, 56, 0.90), (55, 57, 0.80), (56, 59, 0.90),
    (57, 58, 0.80), (60, 62, 0.70), (63, 64, 0.80),

    # ── Intra Groupe E : Market Structure (7 arêtes) ─────────────────────────
    (65, 66, 0.80), (67, 69, 0.70), (68, 69, 0.70),
    (67, 68, 0.70), (71, 72, 0.90), (70, 73, 0.60),
    (65, 74, 0.70),

    # ── Intra Groupe F : TradingView (9 arêtes) ──────────────────────────────
    (75, 76, 0.90), (75, 77, 0.90), (75, 84, 0.90),
    (76, 78, 0.90), (76, 79, 0.90), (76, 80, 0.80),
    (77, 81, 0.80), (77, 82, 0.70), (83, 84, 0.80),

    # ── Intra Groupe G : External (8 arêtes) ─────────────────────────────────
    (85, 86, 0.90), (85, 87, 0.80), (87, 88, 0.80),
    (89, 91, 0.70), (93, 94, 0.60), (97, 98, 0.80),
    (85, 99, 0.80), (97, 99, 0.70),

    # ── Croisé A-B : Price-Volume (10 arêtes) ────────────────────────────────
    (9,  20, 0.80), (0,  21, 0.70), (9,  22, 0.70),
    (0,  23, 0.80), (12, 26, 0.70), (12, 25, 0.70),
    (0,  30, 0.60), (12, 29, 0.60), (17, 33, 0.70),
    (0,  34, 0.80),

    # ── Croisé A-C : Price-Momentum (10 arêtes) ──────────────────────────────
    (0,  35, 0.80), (0,  39, 0.80), (0,  51, 0.80),
    (12, 47, 0.90), (12, 49, 0.90), (9,  40, 0.70),
    (4,  35, 0.70), (4,  39, 0.80),
    (17, 41, 0.80), (11, 37, 0.70),

    # ── Croisé A-D : Price-Volatilité (4 arêtes) ─────────────────────────────
    (0,  55, 0.60), (9,  57, 0.50),
    (6,  55, 0.80), (12, 58, 0.50),

    # ── Croisé A-E : Price-Structure (8 arêtes) ──────────────────────────────
    (0,  65, 0.90), (0,  66, 0.80), (14, 65, 0.80),
    (16, 74, 0.70), (12, 66, 0.70), (18, 68, 0.80),
    (19, 67, 0.80), (13, 65, 0.70),

    # ── Croisé A-F : Price-TradingView (5 arêtes) ────────────────────────────
    (0,  75, 0.80), (4,  77, 0.80), (12, 84, 0.70),
    (0,  77, 0.80), (11, 75, 0.70),

    # ── Croisé A-G : Price-External (5 arêtes) ───────────────────────────────
    (0,  91, 0.60), (9,  87, 0.60), (12, 99, 0.70),
    (17, 88, 0.70), (0,  96, 0.50),

    # ── Croisé B-C : Volume-Momentum (8 arêtes) ──────────────────────────────
    (20, 46, 0.70), (22, 46, 0.80), (23, 40, 0.70),
    (34, 35, 0.60), (24, 46, 0.80), (30, 51, 0.70),
    (31, 54, 0.60), (27, 49, 0.60),

    # ── Croisé B-D : Volume-Volatilité (4 arêtes) ────────────────────────────
    (20, 57, 0.60), (33, 56, 0.80),
    (34, 58, 0.50), (28, 57, 0.60),

    # ── Croisé B-E : Volume-Structure (3 arêtes) ─────────────────────────────
    (23, 65, 0.70), (30, 66, 0.60), (33, 74, 0.60),

    # ── Croisé B-F : Volume-TradingView (3 arêtes) ───────────────────────────
    (20, 83, 0.70), (22, 83, 0.80), (23, 77, 0.60),

    # ── Croisé B-G : Volume-External (5 arêtes) ──────────────────────────────
    (22, 88, 0.80), (25, 89, 0.60), (28, 85, 0.50),
    (34, 87, 0.70), (27, 99, 0.60),

    # ── Croisé C-D : Momentum-Volatilité (6 arêtes) ──────────────────────────
    (35, 58, 0.50), (52, 58, 0.70), (40, 57, 0.50),
    (38, 55, 0.70), (43, 56, 0.60), (54, 64, 0.50),

    # ── Croisé C-E : Momentum-Structure (5 arêtes) ───────────────────────────
    (52, 65, 0.90), (51, 66, 0.80), (39, 65, 0.70),
    (35, 71, 0.60), (42, 73, 0.50),

    # ── Croisé C-F : Momentum-TradingView (8 arêtes) ─────────────────────────
    (78, 35, 0.90), (79, 39, 0.90), (80, 42, 0.90),
    (81, 52, 0.90), (76, 35, 0.80), (76, 40, 0.80),
    (77, 51, 0.70), (84, 49, 0.70),

    # ── Croisé C-G : Momentum-External (4 arêtes) ────────────────────────────
    (35, 89, 0.60), (52, 99, 0.60),
    (40, 87, 0.60), (37, 88, 0.60),

    # ── Croisé D-E : Volatilité-Structure (4 arêtes) ─────────────────────────
    (55, 65, 0.60), (56, 66, 0.70), (57, 74, 0.50),
    (58, 65, 0.60),

    # ── Croisé D-F : Volatilité-TradingView (3 arêtes) ───────────────────────
    (55, 82, 0.80), (56, 82, 0.90), (57, 84, 0.50),

    # ── Croisé D-G : Volatilité-External (4 arêtes) ──────────────────────────
    (55, 86, 0.60), (58, 89, 0.50), (57, 95, 0.60),
    (56, 99, 0.50),

    # ── Croisé E-F : Structure-TradingView (3 arêtes) ────────────────────────
    (65, 77, 0.80), (66, 75, 0.70), (71, 84, 0.60),

    # ── Croisé E-G : Structure-External (3 arêtes) ───────────────────────────
    (65, 99, 0.70), (66, 91, 0.60), (73, 94, 0.50),

    # ── Croisé F-G : TradingView-External (5 arêtes) ─────────────────────────
    (75, 85, 0.70), (84, 99, 0.80), (75, 97, 0.60),
    (76, 89, 0.50), (77, 91, 0.50),
]

assert len(EDGES) == 180, f"Expected 180 edges, got {len(EDGES)}"


# ══════════════════════════════════════════════════════════════════════════════
# POIDS DES NŒUDS (importance relative)
# ══════════════════════════════════════════════════════════════════════════════

NODE_WEIGHTS: Final[np.ndarray] = np.array([
    # A: Price Action (0-19) — importance élevée (données temps réel)
    1.2, 1.0, 1.0, 0.9, 1.1, 1.0, 0.9, 0.8, 0.8,
    1.2, 1.1, 1.0, 1.1, 0.9, 1.0, 1.0, 0.9, 0.8, 0.8, 0.8,

    # B: Volume/Flow (20-34) — importance moyenne-haute
    1.0, 0.9, 1.1, 0.9, 0.8,
    0.7, 0.7, 0.8, 0.6, 0.7,
    0.8, 0.6, 0.8, 1.0, 1.1,

    # C: Momentum (35-54) — importance élevée
    1.2, 1.0, 1.0, 0.7, 1.1,
    1.1, 1.0, 0.9, 0.9, 0.7,
    0.8, 0.9, 1.0, 0.9, 1.0,
    0.8, 0.9, 1.1, 0.8, 0.7,

    # D: Volatilité (55-64) — contexte, importance moyenne
    0.8, 0.9, 0.7, 0.6, 0.7,
    0.6, 0.6, 0.6, 0.6, 0.7,

    # E: Market Structure (65-74) — importance moyenne
    1.0, 0.9, 0.8, 0.8, 0.7,
    0.6, 0.9, 0.9, 0.7, 0.7,

    # F: TradingView (75-84) — importance élevée (agrégation externe)
    1.3, 1.2, 1.2, 1.1, 1.1,
    1.0, 1.0, 0.9, 0.8, 1.2,

    # G: External (85-99) — poly_edge = maximum !
    1.5, 1.2, 1.1, 1.2, 0.8,   # 85-89 (85=poly_edge = plus haut)
    0.7, 0.7, 0.6, 0.5, 0.5,   # 90-94
    0.7, 0.6, 0.7, 0.6, 1.0,   # 95-99
], dtype=np.float64)

assert len(NODE_WEIGHTS) == 100, f"Expected 100 weights, got {len(NODE_WEIGHTS)}"


# ══════════════════════════════════════════════════════════════════════════════
# RÉSULTAT DU FORCE-GRAPH
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class GraphConsensus:
    field: float              # Champ moyen [-1, +1]
    convergence: float        # |field| ∈ [0, 1] — force du consensus
    direction: str            # "BULL" | "BEAR" | "NEUTRAL"
    is_tradeable: bool        # convergence ≥ seuil ET signaux non contradictoires
    node_values: np.ndarray   # État final des 100 nœuds après propagation
    contradiction_score: float  # 0=tous alignés, 1=totalement contradictoire

    @property
    def signal_score(self) -> float:
        """Score de trading ∈ [-1, +1]. >0 = BULL, <0 = BEAR."""
        return self.field


# ══════════════════════════════════════════════════════════════════════════════
# FORCE-GRAPH ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class ForceGraph:
    """
    Moteur force-graph 100 nœuds / 180 connexions.

    Usage :
        graph = ForceGraph()
        graph.set_node(0, 0.8)    # trend_direction = fortement haussier
        graph.set_node(35, 0.6)   # rsi_14 = modérément haussier
        consensus = graph.compute()
    """

    def __init__(self) -> None:
        self._n = 100
        self._values = np.zeros(self._n, dtype=np.float64)
        self._weights = NODE_WEIGHTS.copy()

        # Matrice d'adjacence pondérée (sparse via arrays CSR-like)
        # On garde une liste de (i, j, w) pour la multiplication rapide
        self._adj = np.zeros((self._n, self._n), dtype=np.float64)
        for i, j, w in EDGES:
            self._adj[i, j] = w
            self._adj[j, i] = w  # graphe non-dirigé

        # Index par nom de nœud pour get_node/set_node par nom
        self._name_to_idx: dict[str, int] = {
            name: idx for idx, name in enumerate(NODE_NAMES)
        }

    # ── API publique ──────────────────────────────────────────────────────────

    def set_node(self, idx: int, value: float) -> None:
        """Fixe la valeur d'un nœud. value ∈ [-1, +1]."""
        self._values[idx] = max(-1.0, min(1.0, value))

    def set_by_name(self, name: str, value: float) -> None:
        """Fixe la valeur d'un nœud par son nom."""
        idx = self._name_to_idx.get(name)
        if idx is not None:
            self.set_node(idx, value)

    def get_node(self, idx: int) -> float:
        return float(self._values[idx])

    def reset(self) -> None:
        """Remet tous les nœuds à 0."""
        self._values[:] = 0.0

    def bulk_set(self, updates: dict[str, float]) -> None:
        """Met à jour plusieurs nœuds en une fois (dict nom → valeur)."""
        for name, val in updates.items():
            self.set_by_name(name, val)

    # ── Propagation ───────────────────────────────────────────────────────────

    def _propagate(
        self,
        n_iter: int = FORCE_GRAPH_ITERATIONS,
        alpha: float = FORCE_GRAPH_ALPHA,
    ) -> np.ndarray:
        """
        Propage les influences entre nœuds voisins.

        Chaque itération :
            v_i(t+1) = tanh(v_i(t) + α * Σ_j (w_ij * v_j(t)))

        Vectorisé : l'opération centrale = matrice × vecteur O(N²)
        mais seules 180 entrées sont non-nulles → rapide même en dense.
        """
        v = self._values.copy()
        for _ in range(n_iter):
            influence = self._adj @ v           # O(180) non-zeros
            v = np.tanh(v + alpha * influence)
        return v

    # ── Calcul du consensus ───────────────────────────────────────────────────

    def compute(
        self,
        threshold: float = FORCE_GRAPH_CONVERGENCE_THRESHOLD,
    ) -> GraphConsensus:
        """
        Lance la propagation et calcule le consensus BULL/BEAR.

        Returns:
            GraphConsensus avec field, convergence, direction, is_tradeable.
        """
        propagated = self._propagate()

        # Champ pondéré moyen
        total_weight = np.sum(self._weights)
        field = float(np.dot(self._weights, propagated)) / total_weight
        convergence = abs(field)

        # Détection de contradiction : dispersion des nœuds forts
        strong_mask = np.abs(propagated) > 0.3
        if np.sum(strong_mask) > 0:
            strong_vals = propagated[strong_mask]
            # Contradiction = mix de signaux forts de signes opposés
            bull_ratio = float(np.sum(strong_vals > 0)) / len(strong_vals)
            bear_ratio = 1.0 - bull_ratio
            contradiction = 1.0 - abs(bull_ratio - bear_ratio)
        else:
            contradiction = 0.0

        # Direction
        if convergence < 0.15:
            direction = "NEUTRAL"
        elif field > 0:
            direction = "BULL"
        else:
            direction = "BEAR"

        # Tradeable : convergence suffisante ET peu de contradiction
        is_tradeable = (
            convergence >= threshold
            and contradiction < 0.4
            and direction != "NEUTRAL"
        )

        return GraphConsensus(
            field=field,
            convergence=convergence,
            direction=direction,
            is_tradeable=is_tradeable,
            node_values=propagated,
            contradiction_score=contradiction,
        )

    # ── Diagnostic ────────────────────────────────────────────────────────────

    def top_contributors(self, consensus: GraphConsensus, n: int = 10) -> list[tuple[str, float]]:
        """Retourne les N nœuds qui contribuent le plus au consensus."""
        contributions = self._weights * consensus.node_values
        indices = np.argsort(np.abs(contributions))[::-1][:n]
        return [(NODE_NAMES[i], float(contributions[i])) for i in indices]
