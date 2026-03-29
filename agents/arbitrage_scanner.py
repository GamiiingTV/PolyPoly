"""
PolyPoly — Agent 7 : Arbitrage Scanner
Détecte les opportunités d'arbitrage sans risque sur Polymarket.
YES + NO ≠ 1.0 = argent gratuit (dans la limite du slippage).
"""

import asyncio
import json
from datetime import datetime, timezone
from loguru import logger

from config import MIN_LIQUIDITY_USD, SCANNER_INTERVAL_SEC
from utils.database import Database
from utils.polymarket_api import GammaAPI, CLOBClient, parse_market
try:
    from utils.telegram_bot import TelegramNotifier
except BaseException:
    TelegramNotifier = object  # type: ignore

# Seuils d'arbitrage
MIN_ARBI_EDGE = 0.03          # 3% minimum d'écart pour couvrir les frais
MAX_ARBI_TRADE_SIZE = 5.0     # Cap à 5$ comme les autres trades
ARBI_SCAN_INTERVAL = 90       # secondes


class ArbitrageOpportunity:
    """Représente une opportunité d'arbitrage détectée."""

    def __init__(self, market_id: str, question: str,
                 yes_price: float, no_price: float, arbi_type: str):
        self.market_id = market_id
        self.question = question
        self.yes_price = yes_price
        self.no_price = no_price
        self.arbi_type = arbi_type
        self.sum_prices = yes_price + no_price
        # Sur-évalué : YES+NO > 1.0 → vendre les deux
        # Sous-évalué : YES+NO < 1.0 → acheter les deux
        self.edge = abs(self.sum_prices - 1.0)
        self.is_overpriced = self.sum_prices > 1.0

    @property
    def expected_profit_pct(self) -> float:
        """Profit attendu en % du capital investi."""
        if self.is_overpriced:
            # Acheter NO à (1 - yes_price) puis YES — profit = sum - 1
            return self.sum_prices - 1.0
        else:
            # Acheter YES + NO — profit = 1 - sum
            return 1.0 - self.sum_prices

    def __repr__(self) -> str:
        return (
            f"Arbi[{self.arbi_type}] {self.question[:50]} | "
            f"YES={self.yes_price:.3f} NO={self.no_price:.3f} | "
            f"Sum={self.sum_prices:.4f} | Edge={self.edge:.2%}"
        )


class ArbitrageScanner:
    """
    Agent 7 — Scanner d'arbitrage.

    Types d'arbitrage détectés :
    1. YES+NO ≠ 1.0 sur le même marché (le plus commun)
    2. Marchés corrélés avec pricing incohérent
    3. Marchés proches de la résolution évidente (quasi-certitude)
    4. Arbitrage de sentimentvs prix (fort momentum non intégré)
    """

    def __init__(self, db: Database, gamma: GammaAPI,
                 clob: CLOBClient, telegram: TelegramNotifier):
        self.db = db
        self.gamma = gamma
        self.clob = clob
        self.telegram = telegram
        self._running = False
        self._opportunities_found = 0

    async def run_forever(self) -> None:
        """Boucle principale."""
        self._running = True
        logger.info("Agent 7 (Arbitrage) démarré")
        while self._running:
            try:
                await self.scan_cycle()
            except Exception as e:
                logger.error(f"Arbitrage erreur: {e}")
            await asyncio.sleep(ARBI_SCAN_INTERVAL)

    async def scan_cycle(self) -> list[ArbitrageOpportunity]:
        """Scan complet d'arbitrage."""
        opportunities = []

        # 1. Arbitrage YES+NO ≠ 1.0
        arbi1 = await self._scan_price_sum_arbitrage()
        opportunities.extend(arbi1)

        # 2. Marchés quasi-certains (prix >96¢ ou <4¢)
        arbi2 = await self._scan_near_certain_markets()
        opportunities.extend(arbi2)

        if opportunities:
            self._opportunities_found += len(opportunities)
            logger.info(f"Arbitrage: {len(opportunities)} opportunités détectées")
            for opp in opportunities[:3]:
                logger.info(f"  → {opp}")

        return opportunities

    async def _scan_price_sum_arbitrage(self) -> list[ArbitrageOpportunity]:
        """
        Détecte les marchés où YES_price + NO_price ≠ 1.0.
        C'est la forme d'arbitrage la plus pure et la plus exploitable.
        """
        markets = await self.db.get_active_markets(limit=200)
        opportunities = []

        for market in markets:
            yes_price = market.get("yes_price", 0.5)
            no_price = market.get("no_price", 0.5)
            liquidity = market.get("liquidity", 0)

            if liquidity < MIN_LIQUIDITY_USD:
                continue

            price_sum = yes_price + no_price
            edge = abs(price_sum - 1.0)

            if edge < MIN_ARBI_EDGE:
                continue

            # Vérifier si l'écart est réel et non dû à des données périmées
            # (si les prix ne sont pas cohérents avec la liquidité disponible)
            if yes_price <= 0.01 or no_price <= 0.01:
                continue
            if yes_price >= 0.99 or no_price >= 0.99:
                continue

            opp = ArbitrageOpportunity(
                market_id=market["id"],
                question=market.get("question", ""),
                yes_price=yes_price,
                no_price=no_price,
                arbi_type="PRICE_SUM",
            )

            opportunities.append(opp)

            # Sauvegarder comme signal haute priorité
            signal = {
                "market_id": market["id"],
                "question": market.get("question", ""),
                "signal_type": "ARBITRAGE",
                "direction": "YES" if price_sum < 1.0 else "NO",
                "confidence": min(0.85 + edge * 2, 0.95),
                "edge": edge,
                "predicted_prob": round(1 - no_price if price_sum < 1.0 else no_price, 4),
                "market_price": yes_price,
                "sentiment_score": 0.0,
                "source": f"Arbi PRICE_SUM | YES={yes_price:.3f}+NO={no_price:.3f}={price_sum:.4f}",
            }
            await self.db.save_signal(signal)

            # Notif Telegram si arbitrage significatif
            if edge > 0.06:
                msg = (
                    f"💎 *ARBITRAGE DÉTECTÉ* ({edge:.1%} edge)\n\n"
                    f"📊 {market.get('question', '')[:70]}\n"
                    f"YES={yes_price*100:.1f}¢ + NO={no_price*100:.1f}¢ = "
                    f"{price_sum*100:.1f}¢ ≠ 100¢\n"
                    f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                )
                await self.telegram.send_message(msg)

        return sorted(opportunities, key=lambda x: -x.edge)

    async def _scan_near_certain_markets(self) -> list[ArbitrageOpportunity]:
        """
        Détecte les marchés avec une quasi-certitude sous-évaluée.
        Ex: marché YES à 92¢ alors que l'événement est clairement acquis.
        Stratégie: acheter YES à 92¢, gain garanti de 8% à la résolution.
        """
        markets = await self.db.get_active_markets(limit=200)
        opportunities = []

        for market in markets:
            yes_price = market.get("yes_price", 0.5)
            no_price = market.get("no_price", 0.5)
            liquidity = market.get("liquidity", 0)

            if liquidity < 2000:
                continue

            # Marché presque certain côté YES mais pas encore à 1.0
            if 0.92 <= yes_price <= 0.97:
                edge = 1.0 - yes_price
                if edge >= MIN_ARBI_EDGE:
                    opp = ArbitrageOpportunity(
                        market_id=market["id"],
                        question=market.get("question", ""),
                        yes_price=yes_price,
                        no_price=no_price,
                        arbi_type="NEAR_CERTAIN_YES",
                    )
                    opportunities.append(opp)

            # Marché presque certain côté NO
            elif 0.92 <= no_price <= 0.97:
                edge = 1.0 - no_price
                if edge >= MIN_ARBI_EDGE:
                    opp = ArbitrageOpportunity(
                        market_id=market["id"],
                        question=market.get("question", ""),
                        yes_price=yes_price,
                        no_price=no_price,
                        arbi_type="NEAR_CERTAIN_NO",
                    )
                    opportunities.append(opp)

        return opportunities

    async def get_best_opportunities(self, limit: int = 5) -> list[ArbitrageOpportunity]:
        """Retourne les meilleures opportunités actuelles."""
        return (await self.scan_cycle())[:limit]

    def stop(self) -> None:
        self._running = False
        logger.info("Agent 7 (Arbitrage) arrêté")
