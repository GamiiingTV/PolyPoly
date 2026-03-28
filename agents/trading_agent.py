"""
PolyPoly — Agent 4 : Exécution de trades + Gestion du Risque
Place les ordres sur Polymarket — max $5 par trade, gestion stricte du capital.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional
from loguru import logger

from config import (
    MAX_TRADE_SIZE_USD, CAPITAL_USD, MAX_OPEN_POSITIONS,
    MIN_CONFIDENCE_THRESHOLD, MIN_EDGE_THRESHOLD,
    TRADE_CHECK_INTERVAL_SEC,
)
from utils.database import Database
from utils.polymarket_api import CLOBClient, GammaAPI
try:
    from utils.telegram_bot import TelegramNotifier
except Exception:
    TelegramNotifier = object  # type: ignore


class RiskManager:
    """Gestion stricte du risque — ne trade jamais plus de ce qu'on peut perdre."""

    def __init__(self, db: Database):
        self.db = db

    async def can_trade(self, signal: dict) -> tuple[bool, str]:
        """
        Vérifie si on peut placer ce trade.
        Retourne (True/False, raison).
        """
        # 1. Seuil de confiance
        if signal.get("confidence", 0) < MIN_CONFIDENCE_THRESHOLD:
            return False, f"Confiance insuffisante ({signal['confidence']:.2%} < {MIN_CONFIDENCE_THRESHOLD:.2%})"

        # 2. Edge minimum
        edge = abs(signal.get("edge", 0))
        if edge < MIN_EDGE_THRESHOLD:
            return False, f"Edge insuffisant ({edge:.2%} < {MIN_EDGE_THRESHOLD:.2%})"

        # 3. Nombre de positions ouvertes
        open_trades = await self.db.get_open_trades()
        if len(open_trades) >= MAX_OPEN_POSITIONS:
            return False, f"Trop de positions ouvertes ({len(open_trades)}/{MAX_OPEN_POSITIONS})"

        # 4. Pas déjà une position ouverte sur ce marché
        for t in open_trades:
            if t["market_id"] == signal.get("market_id"):
                return False, "Position déjà ouverte sur ce marché"

        # 5. Capital disponible
        # Récupérer les paramètres dynamiques (Agent 5 peut les modifier)
        dynamic_confidence = await self.db.get_param(
            "min_confidence_threshold", MIN_CONFIDENCE_THRESHOLD
        )
        if signal.get("confidence", 0) < dynamic_confidence:
            return False, f"Seuil dynamique non atteint ({dynamic_confidence:.2%})"

        return True, "OK"

    def compute_trade_size(self, signal: dict, available_capital: float) -> float:
        """
        Calcule la taille optimale du trade (Kelly partiel).
        JAMAIS plus de MAX_TRADE_SIZE_USD (5$).
        """
        confidence = signal.get("confidence", 0.5)
        edge = abs(signal.get("edge", 0))
        market_price = signal.get("market_price", 0.5)

        # Kelly fraction = edge / (1-edge) adapté aux marchés binaires
        if market_price > 0 and market_price < 1:
            kelly = (confidence - (1 - confidence)) / (1 / market_price - 1)
        else:
            kelly = edge

        # Kelly fractionnel (25% du Kelly pour réduire le risque)
        fractional_kelly = max(kelly * 0.25, 0)

        # Taille basée sur le capital
        kelly_size = available_capital * fractional_kelly

        # Cap strict à MAX_TRADE_SIZE_USD
        trade_size = min(kelly_size, MAX_TRADE_SIZE_USD, available_capital * 0.05)
        trade_size = max(trade_size, 1.0)  # Minimum 1$

        return round(trade_size, 2)


class TradingAgent:
    """
    Agent 4 — Exécution et gestion du risque.

    Responsabilités :
    - Reçoit les signaux des agents 1/2/3
    - Vérifie le risque avant chaque trade
    - Place les ordres sur Polymarket (max 5$ par trade)
    - Surveille les positions ouvertes
    - Met à jour le statut des trades résolus
    """

    def __init__(
        self,
        db: Database,
        clob: CLOBClient,
        gamma: GammaAPI,
        telegram: TelegramNotifier,
    ):
        self.db = db
        self.clob = clob
        self.gamma = gamma
        self.telegram = telegram
        self.risk = RiskManager(db)
        self._running = False
        self._simulation_mode = True  # Activé par défaut — désactiver avec clé privée

    async def run_forever(self) -> None:
        """Boucle principale."""
        # Vérifier si on a une clé privée configurée
        from config import POLYMARKET_PRIVATE_KEY
        if POLYMARKET_PRIVATE_KEY and POLYMARKET_PRIVATE_KEY != "0xTON_PRIVATE_KEY_POLYGON_WALLET":
            self._simulation_mode = False
            logger.info("Agent 4 (Trading) en mode LIVE")
        else:
            logger.warning("Agent 4 (Trading) en mode SIMULATION (pas de clé privée)")

        self._running = True
        logger.info("Agent 4 (Trading) démarré")

        while self._running:
            try:
                await self.trading_cycle()
            except Exception as e:
                logger.error(f"Trading erreur: {e}")
                await self.telegram.notify_error(str(e), "Agent 4 - Trading")
            await asyncio.sleep(TRADE_CHECK_INTERVAL_SEC)

    async def trading_cycle(self) -> None:
        """
        Cycle de trading:
        1. Traiter les nouveaux signaux
        2. Vérifier les positions ouvertes (résolution)
        """
        await self._process_pending_signals()
        await self._check_open_positions()

    async def _process_pending_signals(self) -> None:
        """Traite les signaux récents non encore exploités."""
        signals = await self.db.get_recent_signals(limit=30)
        for signal in signals:
            if signal.get("acted_on"):
                continue
            if signal.get("signal_type") != "PREDICTION":
                continue

            can, reason = await self.risk.can_trade(signal)
            if not can:
                logger.debug(f"Trade refusé [{signal['market_id'][:8]}]: {reason}")
                continue

            await self._execute_trade(signal)

    async def _execute_trade(self, signal: dict) -> Optional[int]:
        """Place un trade basé sur un signal validé."""
        market_id = signal["market_id"]
        direction = signal["direction"]
        confidence = signal["confidence"]
        edge = signal["edge"]
        market_price = signal.get("market_price", 0.5)

        # Récupérer le marché pour avoir le token_id
        market = await self.db.get_market(market_id)
        if not market:
            return None

        raw_market = json.loads(market.get("raw_data", "{}"))
        clob_token_ids = raw_market.get("clobTokenIds", [])

        token_id = None
        if clob_token_ids and len(clob_token_ids) >= 2:
            token_id = clob_token_ids[0] if direction == "YES" else clob_token_ids[1]

        # Calculer le capital disponible (simulé ou réel)
        if self._simulation_mode:
            available_capital = CAPITAL_USD
        else:
            try:
                available_capital = await self.clob.get_balance()
            except Exception:
                available_capital = CAPITAL_USD

        trade_size = self.risk.compute_trade_size(signal, available_capital)

        # Prix du token selon la direction
        if direction == "YES":
            price = market.get("yes_price", 0.5)
        else:
            price = market.get("no_price", 0.5)

        order_id = None

        if self._simulation_mode:
            order_id = f"SIM_{market_id[:8]}_{int(datetime.now().timestamp())}"
            logger.info(
                f"[SIMULATION] Trade: {direction} ${trade_size} @ {price:.3f} "
                f"sur {market['question'][:50]}"
            )
        else:
            if not token_id:
                logger.warning(f"Token ID manquant pour {market_id[:8]}")
                return None
            try:
                result = await self.clob.place_market_order(
                    token_id=token_id,
                    side="BUY",
                    amount_usdc=trade_size,
                    price=price,
                )
                order_id = result.get("orderID") or result.get("id", "unknown")
            except Exception as e:
                logger.error(f"Ordre Polymarket échoué: {e}")
                await self.telegram.notify_error(str(e), "Place Order")
                return None

        # Enregistrer dans la DB
        trade = {
            "market_id": market_id,
            "order_id": order_id,
            "direction": direction,
            "size_usd": trade_size,
            "entry_price": price,
            "status": "OPEN",
            "signal_id": signal.get("id"),
            "confidence": confidence,
            "edge": edge,
            "sentiment_score": signal.get("sentiment_score", 0.0),
            "features_json": json.dumps(signal.get("features", [])),
        }

        trade_id = await self.db.save_trade(trade)
        logger.info(f"Trade #{trade_id} ouvert: {direction} ${trade_size} sur {market_id[:8]}")

        # Notifier Telegram
        await self.telegram.notify_trade_placed({
            **trade,
            "question": market.get("question", ""),
        })

        return trade_id

    async def _check_open_positions(self) -> None:
        """Vérifie et met à jour les positions ouvertes."""
        open_trades = await self.db.get_open_trades()
        if not open_trades:
            return

        for trade in open_trades:
            market = await self.db.get_market(trade["market_id"])
            if not market:
                continue

            # Vérifier si le marché est résolu
            end_date_str = market.get("end_date")
            if not end_date_str:
                continue

            try:
                if "Z" in str(end_date_str):
                    end_date_str = str(end_date_str).replace("Z", "+00:00")
                end_date = datetime.fromisoformat(str(end_date_str))
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)

                now = datetime.now(timezone.utc)
                if now < end_date:
                    continue  # Pas encore résolu

                # Marché expiré — récupérer le résultat
                await self._resolve_trade(trade, market)

            except Exception as e:
                logger.debug(f"Check position {trade['id']}: {e}")

    async def _resolve_trade(self, trade: dict, market: dict) -> None:
        """Résout un trade après expiration du marché."""
        if self._simulation_mode:
            # En simulation : résolution basée sur le prix actuel
            current_price = market.get("yes_price", 0.5)
            direction = trade.get("direction", "YES")
            entry_price = trade.get("entry_price", 0.5)
            size_usd = trade.get("size_usd", 5.0)

            # Simulation de résolution (WON si prix > 0.95 pour YES, < 0.05 pour NO)
            if direction == "YES":
                won = current_price >= 0.95
                exit_price = 1.0 if won else 0.0
            else:
                won = current_price <= 0.05
                exit_price = 1.0 if won else 0.0

            if won:
                pnl = size_usd * (1 / entry_price - 1)
            else:
                pnl = -size_usd

            status = "WON" if won else "LOST"
        else:
            # En mode live — récupérer les vraies données de résolution
            raw = json.loads(market.get("raw_data", "{}"))
            resolution = raw.get("resolution")

            direction = trade.get("direction", "YES")
            entry_price = trade.get("entry_price", 0.5)
            size_usd = trade.get("size_usd", 5.0)

            if resolution == "YES" and direction == "YES":
                status, exit_price = "WON", 1.0
                pnl = size_usd * (1 / entry_price - 1)
            elif resolution == "NO" and direction == "NO":
                status, exit_price = "WON", 1.0
                pnl = size_usd * (1 / entry_price - 1)
            else:
                status, exit_price = "LOST", 0.0
                pnl = -size_usd

        updates = {
            "status": status,
            "exit_price": exit_price,
            "pnl": pnl,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.db.update_trade(trade["id"], updates)

        emoji = "WON" if status == "WON" else "LOST"
        logger.info(
            f"Trade #{trade['id']} {emoji}: P&L={pnl:+.2f}$ "
            f"({market['question'][:50]})"
        )

        await self.telegram.notify_trade_result({
            **trade, **updates,
            "question": market.get("question", ""),
        })

    def stop(self):
        self._running = False
        logger.info("Agent 4 (Trading) arrêté")
