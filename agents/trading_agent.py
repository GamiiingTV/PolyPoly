"""
PolyPoly — Agent 4 : Exécution de trades + Gestion du Risque
Place les ordres sur Polymarket — max $5 par trade, gestion stricte du capital.
AMÉLIORATIONS : Stop-loss dynamique, prise de profit, kill switch journalier,
                anti-corrélation, Kelly adaptatif.
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
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
except BaseException:
    TelegramNotifier = object  # type: ignore

# ------------------------------------------------------------------ #
# NOUVEAUX PARAMÈTRES DE GESTION DES POSITIONS
# ------------------------------------------------------------------ #
PROFIT_TAKE_THRESHOLD = 0.80     # Sortir si le prix a bougé vers nous de 80%+ vers 1.0
STOP_LOSS_THRESHOLD   = 0.35     # Couper si prix tombe à <=35% de l'entrée
DAILY_LOSS_LIMIT_USD  = 15.0     # Kill switch : stop si perte journalière > $15
TRAILING_STOP_PCT     = 0.30     # Trailing stop : 30% en dessous du pic
MAX_CORRELATED_MARKETS = 3       # Max 3 marchés dans la même catégorie simultanément
MIN_HOLD_TIME_MINUTES = 5        # Tenir au moins 5 min avant toute décision de sortie


class RiskManager:
    """Gestion stricte du risque — ne trade jamais plus de ce qu'on peut perdre."""

    def __init__(self, db: Database):
        self.db = db
        self._daily_pnl_cache: Optional[float] = None
        self._daily_pnl_date: Optional[str] = None

    async def can_trade(self, signal: dict) -> tuple[bool, str]:
        """Vérifie si on peut placer ce trade. Retourne (True/False, raison)."""

        # 1. Seuil de confiance dynamique
        dynamic_confidence = await self.db.get_param(
            "min_confidence_threshold", MIN_CONFIDENCE_THRESHOLD
        )
        if signal.get("confidence", 0) < dynamic_confidence:
            return False, f"Confiance insuffisante ({signal.get('confidence',0):.2%} < {dynamic_confidence:.2%})"

        # 2. Edge minimum dynamique
        dynamic_edge = await self.db.get_param(
            "min_edge_threshold", MIN_EDGE_THRESHOLD
        )
        edge = abs(signal.get("edge", 0))
        if edge < dynamic_edge:
            return False, f"Edge insuffisant ({edge:.2%} < {dynamic_edge:.2%})"

        # 3. Kill switch journalier
        daily_pnl = await self._get_daily_pnl()
        if daily_pnl <= -DAILY_LOSS_LIMIT_USD:
            return False, f"Kill switch activé: perte journalière ${abs(daily_pnl):.2f} > ${DAILY_LOSS_LIMIT_USD}"

        # 4. Nombre de positions ouvertes
        open_trades = await self.db.get_open_trades()
        if len(open_trades) >= MAX_OPEN_POSITIONS:
            return False, f"Trop de positions ouvertes ({len(open_trades)}/{MAX_OPEN_POSITIONS})"

        # 5. Pas déjà une position sur ce marché
        for t in open_trades:
            if t["market_id"] == signal.get("market_id"):
                return False, "Position déjà ouverte sur ce marché"

        # 6. Anti-corrélation : pas trop de positions dans la même catégorie
        market = await self.db.get_market(signal.get("market_id", ""))
        if market:
            category = market.get("category", "")
            if category:
                same_cat = sum(1 for t in open_trades
                               if self._get_trade_category(t) == category)
                if same_cat >= MAX_CORRELATED_MARKETS:
                    return False, f"Trop de positions corrélées en '{category}' ({same_cat}/{MAX_CORRELATED_MARKETS})"

        # 7. Vérifier catégories blacklistées
        blacklist = await self.db.get_param("blacklisted_categories", [])
        if market and market.get("category", "") in blacklist:
            return False, f"Catégorie blacklistée: {market.get('category')}"

        return True, "OK"

    def _get_trade_category(self, trade: dict) -> str:
        """Récupère la catégorie d'un trade depuis son raw_data."""
        try:
            raw = json.loads(trade.get("raw_data", "{}"))
            return raw.get("category", "")
        except Exception:
            return ""

    async def _get_daily_pnl(self) -> float:
        """Calcule le P&L du jour courant."""
        today = datetime.now().date().isoformat()
        if self._daily_pnl_date == today and self._daily_pnl_cache is not None:
            return self._daily_pnl_cache

        closed = await self.db.get_closed_trades(limit=500)
        today_pnl = sum(
            t.get("pnl", 0) or 0
            for t in closed
            if t.get("resolved_at", "").startswith(today)
        )
        self._daily_pnl_cache = today_pnl
        self._daily_pnl_date = today
        return today_pnl

    def compute_trade_size(self, signal: dict, available_capital: float,
                           win_rate: float = 0.55) -> float:
        """
        Calcule la taille optimale du trade avec Kelly adaptatif.
        Le Kelly s'ajuste en fonction du win rate observé.
        JAMAIS plus de MAX_TRADE_SIZE_USD (5$).
        """
        confidence = signal.get("confidence", 0.5)
        edge = abs(signal.get("edge", 0))
        market_price = signal.get("market_price", 0.5)

        # Kelly adaptatif : utilise le win rate réel si disponible
        effective_win_prob = max(confidence * 0.9, win_rate)

        if market_price > 0.01 and market_price < 0.99:
            odds = 1 / market_price - 1
            kelly = (effective_win_prob * odds - (1 - effective_win_prob)) / odds
        else:
            kelly = edge

        kelly = max(kelly, 0)

        # Fraction Kelly plus conservatrice si win rate bas
        if win_rate < 0.5:
            fraction = 0.15   # Plus prudent si on perd souvent
        elif win_rate > 0.65:
            fraction = 0.30   # Plus agressif si on gagne bien
        else:
            fraction = 0.22

        fractional_kelly = kelly * fraction
        kelly_size = available_capital * fractional_kelly

        # Cap strict : jamais plus de 5$, jamais plus de 5% du capital
        trade_size = min(kelly_size, MAX_TRADE_SIZE_USD, available_capital * 0.05)
        trade_size = max(trade_size, 1.0)

        return round(trade_size, 2)


class SmartExitManager:
    """
    Gère les sorties intelligentes :
    - Prise de profit dès que le marché se déplace fortement en notre faveur
    - Stop-loss pour couper les pertes avant résolution
    - Trailing stop pour protéger les gains
    """

    def __init__(self, db: Database, clob: CLOBClient,
                 telegram: TelegramNotifier, simulation_mode: bool):
        self.db = db
        self.clob = clob
        self.telegram = telegram
        self._simulation_mode = simulation_mode
        # Suivi des prix pics par trade_id
        self._peak_prices: dict[int, float] = {}

    async def check_and_exit(self, trade: dict, current_price: float) -> bool:
        """
        Vérifie si on doit sortir de cette position.
        Retourne True si on a fermé la position.
        """
        trade_id = trade["id"]
        direction = trade.get("direction", "YES")
        entry_price = trade.get("entry_price", 0.5)
        placed_at_str = trade.get("placed_at", "")

        # Respecter le temps de maintien minimum
        if placed_at_str:
            try:
                placed_at = datetime.fromisoformat(
                    placed_at_str.replace("Z", "+00:00")
                ).replace(tzinfo=None)
                if datetime.now() - placed_at < timedelta(minutes=MIN_HOLD_TIME_MINUTES):
                    return False
            except Exception:
                pass

        # Pour NO, inverser le prix (on trade le NO donc le prix du NO est ce qui compte)
        if direction == "NO":
            current_price = 1 - current_price

        # Mettre à jour le prix pic
        if trade_id not in self._peak_prices:
            self._peak_prices[trade_id] = current_price
        peak = max(self._peak_prices.get(trade_id, current_price), current_price)
        self._peak_prices[trade_id] = peak

        # 1. PRISE DE PROFIT : prix très proche de 1.0
        if current_price >= PROFIT_TAKE_THRESHOLD:
            await self._close_position(trade, current_price, "PROFIT_TAKE")
            return True

        # 2. STOP-LOSS : prix trop bas par rapport à l'entrée
        if current_price <= entry_price * STOP_LOSS_THRESHOLD:
            await self._close_position(trade, current_price, "STOP_LOSS")
            return True

        # 3. TRAILING STOP : si on a eu un pic et le prix redescend de >30%
        if peak > entry_price * 1.20:  # On avait au moins 20% de profit
            trailing_floor = peak * (1 - TRAILING_STOP_PCT)
            if current_price < trailing_floor:
                await self._close_position(trade, current_price, "TRAILING_STOP")
                return True

        return False

    async def _close_position(self, trade: dict, exit_price: float, reason: str) -> None:
        """Ferme une position — simulation ou live."""
        trade_id = trade["id"]
        direction = trade.get("direction", "YES")
        entry_price = trade.get("entry_price", 0.5)
        size_usd = trade.get("size_usd", 5.0)

        # Calculer P&L
        if direction == "YES":
            pnl = size_usd * (exit_price / entry_price - 1)
        else:
            pnl = size_usd * ((1 - exit_price) / entry_price - 1)

        status = "WON" if pnl > 0 else "LOST"

        if not self._simulation_mode:
            # En live : annuler la position ou vendre
            order_id = trade.get("order_id")
            if order_id:
                try:
                    await self.clob.cancel_order(order_id)
                except Exception as e:
                    logger.warning(f"Cancel ordre {order_id[:8]}: {e}")

        await self.db.update_trade(trade_id, {
            "status": status,
            "exit_price": exit_price,
            "pnl": round(pnl, 4),
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "error_analysis": f"Sortie automatique: {reason}",
        })

        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
        emoji = "✅" if pnl > 0 else "⛔"
        logger.info(
            f"{emoji} [{reason}] Trade #{trade_id}: {pnl_str} | "
            f"exit={exit_price:.3f} (entry={entry_price:.3f})"
        )

        await self.telegram.notify_trade_result({
            **trade,
            "status": status,
            "exit_price": exit_price,
            "pnl": pnl,
            "question": trade.get("question", ""),
        })

        # Nettoyer le suivi peak
        self._peak_prices.pop(trade_id, None)


class TradingAgent:
    """
    Agent 4 — Exécution et gestion du risque.
    AMÉLIORÉ : Smart exits, Kelly adaptatif, anti-corrélation, kill switch.
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
        self._simulation_mode = True
        self._exit_manager: Optional[SmartExitManager] = None
        self._win_rate_cache: float = 0.55
        self._daily_loss_warned = False
        self._refusal_log: list[tuple[str, str]] = []   # (raison, question)
        self._last_refusal_report: Optional[datetime] = None

    async def run_forever(self) -> None:
        """Boucle principale."""
        from config import POLYMARKET_PRIVATE_KEY
        if POLYMARKET_PRIVATE_KEY and POLYMARKET_PRIVATE_KEY != "0xTON_PRIVATE_KEY_POLYGON_WALLET":
            self._simulation_mode = False
            logger.info("Agent 4 (Trading) en mode LIVE")
        else:
            logger.info("Agent 4 (Trading) en mode PAPER TRADING — accumulation données XGBoost")

        self._exit_manager = SmartExitManager(
            self.db, self.clob, self.telegram, self._simulation_mode
        )

        self._running = True
        logger.info("Agent 4 (Trading) démarré — Smart exits activés")

        while self._running:
            try:
                await self.trading_cycle()
            except Exception as e:
                logger.error(f"Trading erreur: {e}")
                await self.telegram.notify_error(str(e), "Agent 4 - Trading")
            await asyncio.sleep(TRADE_CHECK_INTERVAL_SEC)

    async def trading_cycle(self) -> None:
        """Cycle complet de trading."""
        # Mettre à jour le win rate en cache
        stats = await self.db.get_trade_stats()
        if stats.get("total", 0) >= 10:
            self._win_rate_cache = stats.get("win_rate", 55) / 100

        # Vérifier kill switch
        daily_pnl = await self.risk._get_daily_pnl()
        if daily_pnl <= -DAILY_LOSS_LIMIT_USD:
            if not self._daily_loss_warned:
                self._daily_loss_warned = True
                msg = (
                    f"🚨 *KILL SWITCH ACTIVÉ*\n"
                    f"Perte journalière: ${abs(daily_pnl):.2f} > ${DAILY_LOSS_LIMIT_USD}\n"
                    f"Aucun nouveau trade jusqu'à demain."
                )
                await self.telegram.send_message(msg)
                logger.warning(f"Kill switch: perte journalière ${abs(daily_pnl):.2f}")
        else:
            self._daily_loss_warned = False
            await self._process_pending_signals()

        # Toujours vérifier les positions ouvertes (smart exits)
        await self._check_open_positions()

    async def _process_pending_signals(self) -> None:
        """Traite les signaux récents — priorité aux signaux combinés et arbitrage."""
        signals = await self.db.get_recent_signals(limit=50)
        signals.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        # Priorité : BOOKMAKER > ARBITRAGE > WIKI > COMBINED > PREDICTION > ORDERBOOK > WHALE > SENTIMENT
        priority_order = [
            "BOOKMAKER", "ARBITRAGE", "COHERENCE", "WIKI", "COMBINED",
            "PREDICTION", "ORDERBOOK", "WHALE", "SENTIMENT", "ANOMALY",
        ]
        signals.sort(
            key=lambda x: priority_order.index(x.get("signal_type", "SENTIMENT"))
            if x.get("signal_type") in priority_order else 99
        )

        # Tous les types sont tradeable — BOOKMAKER/WIKI/WHALE même en live
        # car ces signaux sont indépendants du XGBoost
        tradeable_types = [
            "BOOKMAKER", "ARBITRAGE", "COHERENCE", "WIKI", "COMBINED",
            "PREDICTION", "ORDERBOOK", "WHALE", "SMART_MONEY",
        ]
        if self._simulation_mode:
            tradeable_types.append("SENTIMENT")

        # Raisons de refus permanents → marquer le signal pour ne pas re-traiter
        PERMANENT_REFUSAL_KEYWORDS = [
            "Confiance insuffisante", "Edge insuffisant",
            "Trop de positions ouvertes",
        ]

        for signal in signals:
            if signal.get("acted_on"):
                continue
            if signal.get("signal_type") not in tradeable_types:
                # Marquer comme vu pour éviter de le re-traiter indéfiniment
                if signal.get("id"):
                    await self.db.mark_signal_acted_on(signal["id"])
                continue

            can, reason = await self.risk.can_trade(signal)
            if not can:
                logger.info(
                    f"Trade refusé [{signal.get('signal_type','?')}] "
                    f"{signal.get('question','')[:40]}: {reason}"
                )
                self._refusal_log.append((reason, signal.get("question", "")[:50]))
                # Si refus permanent, marquer le signal pour éviter boucle infinie
                if any(kw in reason for kw in PERMANENT_REFUSAL_KEYWORDS):
                    if signal.get("id"):
                        await self.db.mark_signal_acted_on(signal["id"])
                continue

            await self._execute_trade(signal)

        # Rapport de refus toutes les 2 heures
        await self._maybe_send_refusal_report()

    async def _execute_trade(self, signal: dict) -> Optional[int]:
        """Place un trade basé sur un signal validé."""
        market_id = signal["market_id"]
        direction = signal["direction"]
        confidence = signal["confidence"]
        edge = signal["edge"]

        market = await self.db.get_market(market_id)
        if not market:
            return None

        raw_market = json.loads(market.get("raw_data", "{}"))
        clob_token_ids = raw_market.get("clobTokenIds", [])

        token_id = None
        if clob_token_ids and len(clob_token_ids) >= 2:
            token_id = clob_token_ids[0] if direction == "YES" else clob_token_ids[1]

        # Capital disponible
        if self._simulation_mode:
            available_capital = CAPITAL_USD
        else:
            try:
                available_capital = await self.clob.get_balance()
            except Exception:
                available_capital = CAPITAL_USD

        # Kelly adaptatif avec win rate réel
        trade_size = self.risk.compute_trade_size(
            signal, available_capital, self._win_rate_cache
        )

        # Prix selon la direction
        price = market.get("yes_price" if direction == "YES" else "no_price", 0.5)

        order_id = None
        if self._simulation_mode:
            order_id = f"PAPER_{market_id[:8]}_{int(datetime.now().timestamp())}"
            sig_type = signal.get("signal_type", "?")
            logger.info(
                f"[PAPER] {direction} ${trade_size:.2f} @ {price:.3f} "
                f"| {sig_type} conf={confidence:.2%} edge={edge:.2%} "
                f"| {market['question'][:60]}"
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
        logger.info(f"Trade #{trade_id}: {direction} ${trade_size:.2f} | {market_id[:8]} | {market.get('question','')[:50]}")

        # Marquer le signal comme traité pour éviter les doublons
        if signal.get("id"):
            await self.db.mark_signal_acted_on(signal["id"])

        await self.telegram.notify_trade_placed({
            **trade, "question": market.get("question", ""),
        })
        return trade_id

    async def _check_open_positions(self) -> None:
        """Vérifie les positions ouvertes pour smart exits ET résolution."""
        open_trades = await self.db.get_open_trades()
        if not open_trades:
            return

        for trade in open_trades:
            market = await self.db.get_market(trade["market_id"])
            if not market:
                continue

            current_price = market.get("yes_price", 0.5)

            # 1. Smart exits (stop-loss / profit taking)
            if self._exit_manager:
                exited = await self._exit_manager.check_and_exit(trade, current_price)
                if exited:
                    continue

            # 2. Résolution du marché
            await self._check_resolution(trade, market)

    async def _check_resolution(self, trade: dict, market: dict) -> None:
        """Vérifie si le marché est résolu."""
        end_date_str = market.get("end_date")
        if not end_date_str:
            return

        try:
            if "Z" in str(end_date_str):
                end_date_str = str(end_date_str).replace("Z", "+00:00")
            end_date = datetime.fromisoformat(str(end_date_str))
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)

            if datetime.now(timezone.utc) < end_date:
                return

            await self._resolve_trade(trade, market)
        except Exception as e:
            logger.debug(f"Check résolution {trade['id']}: {e}")

    async def _resolve_trade(self, trade: dict, market: dict) -> None:
        """Résout un trade après expiration du marché."""
        current_price = market.get("yes_price", 0.5)
        direction = trade.get("direction", "YES")
        entry_price = trade.get("entry_price", 0.5)
        size_usd = trade.get("size_usd", 5.0)

        if self._simulation_mode:
            if direction == "YES":
                won = current_price >= 0.95
                exit_price = 1.0 if won else 0.0
            else:
                won = current_price <= 0.05
                exit_price = 1.0 if won else 0.0
            pnl = size_usd * (1 / entry_price - 1) if won else -size_usd
        else:
            raw = json.loads(market.get("raw_data", "{}"))
            resolution = raw.get("resolution")
            if resolution == "YES" and direction == "YES":
                status, exit_price = "WON", 1.0
                pnl = size_usd * (1 / entry_price - 1)
            elif resolution == "NO" and direction == "NO":
                status, exit_price = "WON", 1.0
                pnl = size_usd * (1 / entry_price - 1)
            else:
                status, exit_price = "LOST", 0.0
                pnl = -size_usd
            won = status == "WON"

        status = "WON" if won else "LOST"
        updates = {
            "status": status,
            "exit_price": exit_price,
            "pnl": round(pnl, 4),
            "resolved_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.db.update_trade(trade["id"], updates)
        logger.info(f"Trade #{trade['id']} {status}: {pnl:+.2f}$")

        await self.telegram.notify_trade_result({
            **trade, **updates, "question": market.get("question", ""),
        })

    async def _maybe_send_refusal_report(self) -> None:
        """Envoie un résumé des refus toutes les 2h pour diagnostiquer."""
        now = datetime.now()
        if (
            not self._refusal_log
            or (self._last_refusal_report and (now - self._last_refusal_report).seconds < 7200)
        ):
            return
        self._last_refusal_report = now

        from collections import Counter
        reasons = Counter(r for r, _ in self._refusal_log)
        top = reasons.most_common(5)
        lines = ["📋 <b>Rapport trades refusés (2h)</b>\n"]
        for reason, count in top:
            lines.append(f"• {count}× {reason}")

        await self.telegram.send_message("\n".join(lines))
        self._refusal_log.clear()

    def stop(self) -> None:
        self._running = False
        logger.info("Agent 4 (Trading) arrêté")
