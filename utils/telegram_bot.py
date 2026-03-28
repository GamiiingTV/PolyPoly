"""
PolyPoly — Notifications Telegram
Envoie les opportunités, trades et rapports sur ton Telegram.
"""

import asyncio
from datetime import datetime
from typing import Optional

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError
from loguru import logger

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class TelegramNotifier:
    """Gestionnaire de notifications Telegram."""

    def __init__(self):
        self.bot: Optional[Bot] = None
        self.chat_id = TELEGRAM_CHAT_ID
        self._enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

    async def start(self):
        if not self._enabled:
            logger.warning("Telegram non configuré — notifications désactivées")
            return
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        try:
            me = await self.bot.get_me()
            logger.info(f"Telegram connecté: @{me.username}")
            await self.send_message("🤖 *PolyPoly Bot démarré* — Je surveille les marchés...")
        except TelegramError as e:
            logger.error(f"Erreur Telegram: {e}")
            self._enabled = False

    async def send_message(self, text: str, parse_mode: str = ParseMode.MARKDOWN) -> bool:
        if not self._enabled or not self.bot:
            return False
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode,
            )
            return True
        except TelegramError as e:
            logger.error(f"Erreur envoi Telegram: {e}")
            return False

    async def notify_opportunity(self, signal: dict) -> None:
        """Notifie une opportunité détectée."""
        direction_emoji = "🟢" if signal.get("direction") == "YES" else "🔴"
        confidence = signal.get("confidence", 0) * 100
        edge = signal.get("edge", 0) * 100
        market_price = signal.get("market_price", 0) * 100
        predicted_prob = signal.get("predicted_prob", 0) * 100

        msg = (
            f"🎯 *OPPORTUNITÉ DÉTECTÉE*\n\n"
            f"📊 *Marché:* {signal.get('question', 'N/A')[:80]}\n\n"
            f"{direction_emoji} *Direction:* {signal.get('direction', 'N/A')}\n"
            f"💰 *Prix marché:* {market_price:.1f}¢\n"
            f"🧠 *Prob. prédite:* {predicted_prob:.1f}¢\n"
            f"📈 *Edge:* +{edge:.1f}%\n"
            f"🎲 *Confiance:* {confidence:.1f}%\n\n"
            f"📡 *Source:* {signal.get('source', 'N/A')}\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
        await self.send_message(msg)

    async def notify_trade_placed(self, trade: dict) -> None:
        """Notifie qu'un trade a été placé."""
        direction_emoji = "🟢" if trade.get("direction") == "YES" else "🔴"
        msg = (
            f"✅ *TRADE PLACÉ*\n\n"
            f"📊 *Marché:* {trade.get('question', 'N/A')[:80]}\n"
            f"{direction_emoji} *Direction:* {trade.get('direction')}\n"
            f"💵 *Montant:* ${trade.get('size_usd', 0):.2f}\n"
            f"💰 *Prix entrée:* {trade.get('entry_price', 0) * 100:.1f}¢\n"
            f"🎲 *Confiance:* {trade.get('confidence', 0) * 100:.1f}%\n"
            f"🆔 Ordre: `{str(trade.get('order_id', 'N/A'))[:16]}...`\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
        await self.send_message(msg)

    async def notify_trade_result(self, trade: dict) -> None:
        """Notifie le résultat d'un trade (gagné/perdu)."""
        won = trade.get("status") == "WON"
        emoji = "🏆" if won else "💀"
        pnl = trade.get("pnl", 0)
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"

        msg = (
            f"{emoji} *TRADE {'GAGNÉ' if won else 'PERDU'}*\n\n"
            f"📊 *Marché:* {trade.get('question', 'N/A')[:80]}\n"
            f"💵 *P&L:* `{pnl_str}`\n"
            f"📈 *Prix sortie:* {trade.get('exit_price', 0) * 100:.1f}¢\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
        await self.send_message(msg)

    async def notify_daily_report(self, stats: dict) -> None:
        """Rapport quotidien de performance."""
        win_rate = stats.get("win_rate", 0)
        total_pnl = stats.get("total_pnl", 0)
        pnl_str = f"+${total_pnl:.2f}" if total_pnl >= 0 else f"-${abs(total_pnl):.2f}"

        msg = (
            f"📊 *RAPPORT JOURNALIER*\n"
            f"═══════════════════\n"
            f"🏆 *Win rate:* {win_rate:.1f}%\n"
            f"💵 *P&L total:* `{pnl_str}`\n"
            f"📈 *Total trades:* {stats.get('total', 0)}\n"
            f"✅ *Gagnés:* {stats.get('wins', 0)}\n"
            f"❌ *Perdus:* {stats.get('losses', 0)}\n"
            f"🎲 *Confiance moy.:* {stats.get('avg_confidence', 0) * 100:.1f}%\n"
            f"📊 *Edge moyen:* {stats.get('avg_edge', 0) * 100:.1f}%\n"
            f"═══════════════════\n"
            f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        await self.send_message(msg)

    async def notify_anomaly(self, market: dict) -> None:
        """Alerte sur une anomalie de prix détectée."""
        msg = (
            f"⚡ *ANOMALIE DÉTECTÉE*\n\n"
            f"📊 *Marché:* {market.get('question', 'N/A')[:80]}\n"
            f"📈 *Score anomalie:* {market.get('anomaly_score', 0):.2f}\n"
            f"💰 *Prix YES:* {market.get('yes_price', 0) * 100:.1f}¢\n"
            f"📊 *Spread:* {market.get('spread', 0) * 100:.1f}%\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
        await self.send_message(msg)

    async def notify_learning_update(self, pattern: str, action: str) -> None:
        """Notifie une mise à jour de l'apprentissage."""
        msg = (
            f"🧠 *APPRENTISSAGE MIS À JOUR*\n\n"
            f"🔍 *Pattern détecté:* {pattern}\n"
            f"🔧 *Action corrective:* {action}\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
        await self.send_message(msg)

    async def notify_error(self, error: str, context: str = "") -> None:
        """Notifie une erreur critique."""
        msg = (
            f"🚨 *ERREUR BOT*\n\n"
            f"📍 *Contexte:* {context}\n"
            f"❌ *Erreur:* `{error[:200]}`\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
        await self.send_message(msg)
