"""
PolyPoly — Agent 1 : Market Scanner
Scanne 300+ marchés Polymarket, filtre par qualité et détecte les anomalies.
"""

import asyncio
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Optional
from loguru import logger

from config import (
    MIN_LIQUIDITY_USD, MIN_VOLUME_24H_USD,
    MAX_TIME_TO_RESOLUTION_DAYS, MIN_TIME_TO_RESOLUTION_HOURS,
    PRICE_ANOMALY_THRESHOLD, PRICE_ANOMALY_WINDOW_MIN,
    SPREAD_ANOMALY_THRESHOLD, TARGET_MARKETS_COUNT, SCANNER_INTERVAL_SEC,
    CATEGORY_KEYWORDS,
)
from utils.database import Database
from utils.polymarket_api import GammaAPI, parse_market
try:
    from utils.telegram_bot import TelegramNotifier
except Exception:
    TelegramNotifier = object  # type: ignore


class MarketScanner:
    """
    Agent 1 — Scanner & Filtreur de marchés.

    Responsabilités :
    - Récupère 300+ marchés actifs depuis Polymarket
    - Filtre par liquidité, volume, temps avant résolution
    - Calcule un score d'anomalie pour chaque marché
    - Détecte les mouvements de prix suspects et spread anormaux
    - Met à jour la base de données en continu
    """

    def __init__(self, db: Database, gamma: GammaAPI, telegram: TelegramNotifier):
        self.db = db
        self.gamma = gamma
        self.telegram = telegram
        self._running = False
        self.scanned_count = 0
        self.anomaly_count = 0

    async def run_forever(self) -> None:
        """Boucle principale — tourne H24."""
        self._running = True
        logger.info("Agent 1 (Scanner) démarré")
        while self._running:
            try:
                await self.scan_cycle()
            except Exception as e:
                logger.error(f"Scanner erreur: {e}")
                await self.telegram.notify_error(str(e), "Agent 1 - Scanner")
            await asyncio.sleep(SCANNER_INTERVAL_SEC)

    async def scan_cycle(self) -> list[dict]:
        """Un cycle complet de scan."""
        logger.info("Scanner: démarrage cycle...")

        raw_markets = await self.gamma.get_all_active_markets(TARGET_MARKETS_COUNT)
        filtered = []

        for raw in raw_markets:
            market = parse_market(raw)
            if not self._passes_basic_filters(market):
                continue

            # Enregistrer le prix dans l'historique
            await self.db.record_price(
                market_id=market["id"],
                yes_price=market["yes_price"],
                no_price=market["no_price"],
                spread=market["spread"],
                volume=market["volume_24h"],
            )

            # Détecter la catégorie automatiquement
            if not market.get("category"):
                market["category"] = self._detect_category(market)

            # Calculer le score d'anomalie
            anomaly_score = await self._compute_anomaly_score(market)
            market["anomaly_score"] = anomaly_score

            # Sauvegarder dans la DB
            await self.db.upsert_market(market)
            filtered.append(market)

            # Alerte si forte anomalie
            if anomaly_score > 0.75:
                self.anomaly_count += 1
                logger.warning(
                    f"ANOMALIE [{anomaly_score:.2f}]: {market['question'][:60]}"
                )
                await self.telegram.notify_anomaly(market)

        self.scanned_count = len(filtered)
        logger.info(
            f"Scanner: {self.scanned_count} marchés filtrés, "
            f"{self.anomaly_count} anomalies totales"
        )
        return filtered

    def _passes_basic_filters(self, market: dict) -> bool:
        """Vérifie si le marché passe les critères de base."""
        if not market.get("id") or not market.get("active"):
            return False

        if market.get("liquidity", 0) < MIN_LIQUIDITY_USD:
            return False

        if market.get("volume_24h", 0) < MIN_VOLUME_24H_USD:
            return False

        # Vérifier le temps avant résolution
        end_date_str = market.get("end_date")
        if end_date_str:
            try:
                if "Z" in end_date_str:
                    end_date_str = end_date_str.replace("Z", "+00:00")
                end_date = datetime.fromisoformat(end_date_str)
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                delta = end_date - now

                if delta.total_seconds() < MIN_TIME_TO_RESOLUTION_HOURS * 3600:
                    return False
                if delta.days > MAX_TIME_TO_RESOLUTION_DAYS:
                    return False
            except (ValueError, TypeError):
                pass

        # Filtrer les marchés avec prix extrêmes (>85¢ ou <5¢) — quasi-résolus
        yes_price = market.get("yes_price", 0.5)
        if yes_price > 0.85 or yes_price < 0.05:
            return False

        return True

    async def _compute_anomaly_score(self, market: dict) -> float:
        """
        Calcule un score d'anomalie entre 0.0 et 1.0.
        Plus le score est élevé, plus le marché est intéressant.
        """
        scores = []

        # 1. Score de spread anormal (spread élevé = opportunité potentielle)
        spread = market.get("spread", 0)
        if spread > SPREAD_ANOMALY_THRESHOLD:
            spread_score = min(spread / 0.30, 1.0)
        else:
            spread_score = 0.0
        scores.append(spread_score * 0.25)

        # 2. Score de mouvement de prix récent
        price_movement_score = await self._compute_price_movement_score(
            market["id"], market["yes_price"]
        )
        scores.append(price_movement_score * 0.35)

        # 3. Score de liquidité relative (moins liquide = plus exploitable)
        liq = market.get("liquidity", 0)
        if 1000 <= liq <= 50000:
            liq_score = 0.5
        elif liq < 1000:
            liq_score = 0.2
        else:
            liq_score = 0.3
        scores.append(liq_score * 0.15)

        # 4. Score basé sur le prix (marchés proches de 50% = incertains)
        yes_price = market.get("yes_price", 0.5)
        price_uncertainty = 1 - abs(yes_price - 0.5) * 2
        scores.append(price_uncertainty * 0.25)

        return min(sum(scores), 1.0)

    async def _compute_price_movement_score(
        self, market_id: str, current_price: float
    ) -> float:
        """Détecte les mouvements de prix suspects sur la fenêtre récente."""
        history = await self.db.get_price_history(market_id, PRICE_ANOMALY_WINDOW_MIN)

        if len(history) < 3:
            return 0.0

        prices = [h["yes_price"] for h in history]
        oldest_price = prices[0]

        if oldest_price <= 0:
            return 0.0

        movement = abs(current_price - oldest_price) / oldest_price

        if movement >= PRICE_ANOMALY_THRESHOLD:
            # Normalise entre 0 et 1
            return min(movement / 0.30, 1.0)

        # Volatilité intra-période
        if len(prices) >= 5:
            volatility = float(np.std(prices))
            if volatility > 0.05:
                return min(volatility / 0.15, 1.0) * 0.5

        return 0.0

    @staticmethod
    def _detect_category(market: dict) -> str:
        """Détecte la catégorie du marché via mots-clés dans la question."""
        text = (market.get("question", "") + " " + market.get("description", "")).lower()
        scores: dict[str, int] = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[category] = score
        if not scores:
            return "other"
        return max(scores, key=lambda k: scores[k])

    async def get_top_markets(self, n: int = 20) -> list[dict]:
        """Retourne les N meilleurs marchés par score d'anomalie."""
        return await self.db.get_active_markets(
            min_liquidity=MIN_LIQUIDITY_USD, limit=n
        )

    def stop(self):
        self._running = False
        logger.info("Agent 1 (Scanner) arrêté")
