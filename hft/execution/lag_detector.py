"""
HFT Lag Detector — Détection du micro-déphasage spot Binance / CLOB Polymarket.

Principe :
  BTC monte de 0.3% sur Binance à T+0ms.
  Polymarket n'a pas encore repricé à T+200ms.
  → Fenêtre d'arbitrage : acheter YES avant le repricing.

Ce module mesure et détecte ce déphasage en temps réel.
Il estime aussi la probabilité vraie de résolution basée sur la dynamique prix.
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from loguru import logger

from hft.config_hft import (
    LAG_WINDOW,
    MIN_LAG_MS,
    MAX_LAG_MS,
    MIN_PRICE_MOVE_PCT,
    MIN_EDGE_PCT,
)


# ── Structures ────────────────────────────────────────────────────────────────

@dataclass
class PriceEvent:
    price: float
    timestamp_ms: int
    source: str   # "binance" | "polymarket"


@dataclass
class LagMeasurement:
    lag_ms: float       # délai mesuré Binance→Polymarket
    price_move_pct: float
    direction: int      # +1 hausse, -1 baisse
    timestamp_ms: int


@dataclass
class EdgeWindow:
    """Représente une fenêtre d'arbitrage détectée."""
    direction: str          # "BULL" ou "BEAR"
    binance_move_pct: float # amplitude du mouvement Binance
    poly_old_price: float   # prix Polymarket avant repricing
    estimated_fair_price: float  # notre estimation du juste prix
    edge_pct: float         # edge = |estimated - current| / current
    opened_at_ms: int       # timestamp d'ouverture
    age_ms: int = 0

    @property
    def is_expired(self) -> bool:
        return self.age_ms > MAX_LAG_MS

    def refresh(self) -> None:
        self.age_ms = int(time.time() * 1000) - self.opened_at_ms


# ── Lag Detector ──────────────────────────────────────────────────────────────

class LagDetector:
    """
    Détecte le déphasage entre Binance spot et Polymarket CLOB.

    Métriques calculées :
      - lag_ms moyen Binance → Polymarket (rolling window)
      - fenêtres d'arbitrage ouvertes
      - probabilité estimée de résolution YES/NO
    """

    def __init__(self) -> None:
        # Historique des events
        self._binance_events: deque[PriceEvent] = deque(maxlen=500)
        self._poly_events: deque[PriceEvent] = deque(maxlen=200)

        # Mesures de lag
        self._lag_measurements: deque[LagMeasurement] = deque(maxlen=LAG_WINDOW)

        # Fenêtre d'arbitrage en cours
        self._current_edge: Optional[EdgeWindow] = None

        # Référence pour détecter les mouvements Binance
        self._binance_ref_price: float = 0.0
        self._binance_ref_ts: int = 0
        self._poly_last_price: float = 0.5
        self._poly_last_ts: int = 0

        # Statistiques
        self._total_windows_detected: int = 0
        self._avg_lag_cache: float = 0.0
        self._cache_ts: float = 0.0

    # ── Ingestion des events ──────────────────────────────────────────────────

    def on_binance_tick(self, price: float, ts_ms: int) -> None:
        """Enregistre un tick Binance et cherche un mouvement exploitable."""
        event = PriceEvent(price=price, timestamp_ms=ts_ms, source="binance")
        self._binance_events.append(event)

        if self._binance_ref_price == 0:
            self._binance_ref_price = price
            self._binance_ref_ts = ts_ms
            return

        # Mesure le mouvement depuis la référence
        move_pct = (price - self._binance_ref_price) / self._binance_ref_price

        # Réinitialise la référence régulièrement (toutes les 10s)
        if ts_ms - self._binance_ref_ts > 10_000:
            self._binance_ref_price = price
            self._binance_ref_ts = ts_ms

        # Mouvement significatif → ouvre fenêtre si pas déjà ouverte
        if abs(move_pct) >= MIN_PRICE_MOVE_PCT:
            self._try_open_edge_window(price, move_pct, ts_ms)

    def on_polymarket_price(self, yes_price: float, ts_ms: int) -> None:
        """Enregistre un update de prix Polymarket CLOB."""
        old_poly = self._poly_last_price
        self._poly_events.append(
            PriceEvent(price=yes_price, timestamp_ms=ts_ms, source="polymarket")
        )

        # Mesure le lag si on a un event Binance récent
        if self._binance_events and abs(yes_price - old_poly) > 0.005:
            # Polymarket vient de repriser → calculer le lag
            last_binance = self._binance_events[-1]
            lag = ts_ms - last_binance.timestamp_ms
            if 0 < lag < MAX_LAG_MS * 2:
                move = (last_binance.price - self._binance_ref_price) / (self._binance_ref_price + 1e-8)
                measurement = LagMeasurement(
                    lag_ms=float(lag),
                    price_move_pct=move,
                    direction=1 if move > 0 else -1,
                    timestamp_ms=ts_ms,
                )
                self._lag_measurements.append(measurement)
                logger.debug(f"Lag mesuré: {lag:.0f}ms pour Δ={move*100:+.2f}%")

        # Ferme la fenêtre si Polymarket a repricé
        if self._current_edge and abs(yes_price - self._current_edge.poly_old_price) > 0.01:
            logger.debug(
                f"Fenêtre fermée : Polymarket a repricé "
                f"{self._current_edge.poly_old_price:.4f} → {yes_price:.4f}"
            )
            self._current_edge = None

        self._poly_last_price = yes_price
        self._poly_last_ts = ts_ms

    # ── Analyse principale ────────────────────────────────────────────────────

    def _try_open_edge_window(
        self, binance_price: float, move_pct: float, ts_ms: int
    ) -> None:
        """
        Tente d'ouvrir une fenêtre d'arbitrage.
        Conditions :
          - Mouvement Binance ≥ MIN_PRICE_MOVE_PCT
          - Polymarket n'a pas encore bougé (age > MIN_LAG_MS)
          - Pas déjà dans une fenêtre active
        """
        if self._current_edge and not self._current_edge.is_expired:
            self._current_edge.refresh()
            return

        # Vérifier que Polymarket n'a pas encore repricé
        now_ms = ts_ms
        poly_age_ms = now_ms - self._poly_last_ts
        if poly_age_ms < MIN_LAG_MS:
            return   # Polymarket vient de repriser, trop tard

        # Calculer notre edge
        poly_yes_price = self._poly_last_price
        estimated_fair = self._estimate_fair_price(binance_price, move_pct)
        edge = abs(estimated_fair - poly_yes_price)

        if edge < MIN_EDGE_PCT:
            return   # Pas assez d'edge

        direction = "BULL" if move_pct > 0 else "BEAR"

        self._current_edge = EdgeWindow(
            direction=direction,
            binance_move_pct=move_pct,
            poly_old_price=poly_yes_price,
            estimated_fair_price=estimated_fair,
            edge_pct=edge,
            opened_at_ms=ts_ms,
        )
        self._total_windows_detected += 1
        logger.info(
            f"Fenêtre arbitrage {direction}: "
            f"BTC {move_pct*100:+.3f}% | "
            f"Poly={poly_yes_price:.4f} → fair={estimated_fair:.4f} | "
            f"edge={edge*100:.2f}% | "
            f"lag_poly={poly_age_ms:.0f}ms"
        )

    def _estimate_fair_price(self, spot_price: float, move_pct: float) -> float:
        """
        Estime la probabilité vraie YES (BTC plus haut dans 5 min).

        Modèle simplifié basé sur :
          - La direction et amplitude du mouvement récent
          - La probabilité de base (marché efficient = 50%)
          - Le momentum (les mouvements tendent à continuer à court terme)
        """
        # Probabilité de base du marché
        base_prob = self._poly_last_price

        # Ajustement basé sur le momentum BTC
        # Mouvement de +0.3% → probabilité hausse augmente de ~10%
        # Basé sur la distribution empirique des mouvements BTC 5M
        momentum_adj = math.tanh(move_pct / 0.003) * 0.15

        # Régression vers la moyenne : les grands mouvements tendent à se corriger
        if abs(move_pct) > 0.005:
            # Fort mouvement → possible mean-reversion
            momentum_adj *= (1 - abs(move_pct) / 0.01)

        fair_prob = base_prob + momentum_adj

        # Contraindre entre 0.05 et 0.95
        return max(0.05, min(0.95, fair_prob))

    # ── API publique ──────────────────────────────────────────────────────────

    def get_current_edge(self) -> Optional[EdgeWindow]:
        """Retourne la fenêtre d'arbitrage active, ou None."""
        if self._current_edge:
            self._current_edge.refresh()
            if self._current_edge.is_expired:
                logger.debug("Fenêtre expirée (timeout)")
                self._current_edge = None
        return self._current_edge

    def get_avg_lag_ms(self) -> float:
        """Lag moyen mesuré Binance → Polymarket (ms)."""
        now = time.time()
        if now - self._cache_ts < 5.0:
            return self._avg_lag_cache
        if not self._lag_measurements:
            return 500.0   # valeur par défaut conservative
        recent = [m.lag_ms for m in self._lag_measurements
                  if int(time.time() * 1000) - m.timestamp_ms < 300_000]
        self._avg_lag_cache = float(np.mean(recent)) if recent else 500.0
        self._cache_ts = now
        return self._avg_lag_cache

    def get_estimated_fair_price(self) -> float:
        """Dernier prix juste estimé (ou 0.5 si pas d'info)."""
        if self._current_edge:
            return self._current_edge.estimated_fair_price
        return self._poly_last_price

    def is_arbitrage_window_open(self) -> bool:
        """True si une fenêtre d'arbitrage exploitable est ouverte."""
        edge = self.get_current_edge()
        return edge is not None and not edge.is_expired

    def get_poly_update_age_ms(self) -> int:
        """Âge du dernier update Polymarket en ms."""
        if self._poly_last_ts == 0:
            return 999_999
        return int(time.time() * 1000) - self._poly_last_ts

    def get_stats(self) -> dict:
        return {
            "avg_lag_ms": self.get_avg_lag_ms(),
            "total_windows": self._total_windows_detected,
            "active_window": self._current_edge is not None,
            "poly_update_age_ms": self.get_poly_update_age_ms(),
            "measurements_count": len(self._lag_measurements),
        }
