"""
Resolution Sniper — stratégie complémentaire au HFT repricing.

Logique :
  Les marchés BTC 5-min Polymarket résolvent toutes les 5 minutes.
  Dans les 60-90 dernières secondes, si BTC a clairement bougé depuis
  l'ouverture du marché, la probabilité de résolution est ~80-90%.
  On achète YES (ou NO) à 87 cents → gagne 0.13/token si résout OK.

  Calcul du temps restant :
    seconds_into_window = now_seconds % WINDOW_SEC
    seconds_left        = WINDOW_SEC - seconds_into_window
    → Si seconds_left < SNIPE_THRESHOLD → fenêtre de snipe ouverte

  Win rate modélisé :
    P(win) = sigmoid(|btc_move_4c| / 0.002 - 0.5) × 0.22 + 0.70
    move=0.15% → ~75%  |  move=0.25% → ~82%  |  move=0.40% → ~89%
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Optional

WINDOW_SEC       = 5 * 60       # Polymarket BTC 5-min market window
SNIPE_THRESHOLD  = 90           # secondes avant résolution pour entrer
SNIPE_ENTRY      = 0.87         # prix d'entrée (87 cents) YES ou NO
SNIPE_MIN_MOVE   = 0.0015       # mouvement BTC min depuis ouverture (0.15%)
SNIPE_COOLDOWN   = WINDOW_SEC   # 1 snipe max par fenêtre de marché


@dataclass
class SnipeSignal:
    direction: str        # "BULL" | "BEAR"
    entry_price: float    # prix token (0.87)
    seconds_left: float   # temps avant résolution
    move_pct: float       # mouvement BTC depuis début fenêtre
    size_usd: float       # montant à placer


class ResolutionSniper:
    """
    Détecte et génère des signaux de résolution sniping.
    À appeler à chaque tick Binance avec le prix BTC actuel.
    """

    def __init__(self, trade_size_usd: float = 10.0) -> None:
        self._size     = trade_size_usd
        self._last_ts  = 0       # timestamp dernier snipe
        # Prix BTC au début de chaque fenêtre de marché (approximation)
        self._window_open_price: float = 0.0
        self._last_window_idx: int = -1

    def update_size(self, new_size: float) -> None:
        self._size = new_size

    def evaluate(
        self,
        btc_price: float,
        btc_closes_4c: list[float],   # 4 derniers closes 5M
        poly_yes_price: float,
    ) -> Optional[SnipeSignal]:
        """
        Retourne un SnipeSignal si on est dans la fenêtre de snipe
        et que les conditions sont remplies. None sinon.
        """
        now      = time.time()
        sec_into = now % WINDOW_SEC
        sec_left = WINDOW_SEC - sec_into

        # Cooldown : 1 snipe par fenêtre de 5 minutes
        window_idx = int(now // WINDOW_SEC)
        if window_idx == self._last_window_idx:
            return None

        # Pas dans la fenêtre de snipe
        if sec_left > SNIPE_THRESHOLD or sec_left < 5:
            return None

        # Calcul du mouvement BTC depuis l'ouverture estimée de la fenêtre
        if len(btc_closes_4c) < 2:
            return None

        # Approximation : prix d'ouverture de la fenêtre = close il y a 4 bougies
        open_price = btc_closes_4c[0]
        if open_price <= 0:
            return None

        move_pct = (btc_price - open_price) / open_price

        # Mouvement insuffisant
        if abs(move_pct) < SNIPE_MIN_MOVE:
            return None

        direction = "BULL" if move_pct > 0 else "BEAR"

        # Vérification cohérence avec le prix Polymarket courant
        # Si BTC monte mais YES est déjà à 0.92+, trop tard — marge trop faible
        if direction == "BULL" and poly_yes_price > 0.92:
            return None
        if direction == "BEAR" and poly_yes_price < 0.08:
            return None

        self._last_window_idx = window_idx

        return SnipeSignal(
            direction=direction,
            entry_price=SNIPE_ENTRY,
            seconds_left=sec_left,
            move_pct=move_pct,
            size_usd=self._size,
        )

    @staticmethod
    def seconds_to_resolution() -> float:
        """Secondes restantes dans la fenêtre de marché courante."""
        return WINDOW_SEC - (time.time() % WINDOW_SEC)
