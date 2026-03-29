"""
PolyPoly — Notifications Telegram
Utilise l'API HTTP Telegram directement (pas de python-telegram-bot).
"""

import asyncio
import aiohttp
from datetime import datetime
from typing import Optional
from loguru import logger

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_BASE_URL = "https://api.telegram.org/bot{token}/{method}"


class TelegramNotifier:
    """Gestionnaire de notifications Telegram via HTTP direct."""

    def __init__(self):
        self.chat_id = TELEGRAM_CHAT_ID
        self._token = TELEGRAM_BOT_TOKEN
        self._enabled = bool(self._token and self.chat_id)
        self._session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        if not self._enabled:
            logger.warning("Telegram non configuré — notifications désactivées")
            return
        self._session = aiohttp.ClientSession()
        try:
            url = TELEGRAM_BASE_URL.format(token=self._token, method="getMe")
            async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
            if data.get("ok"):
                username = data["result"].get("username", "bot")
                logger.info(f"Telegram connecté: @{username}")
                await self.send_message("🤖 <b>PolyPoly Bot démarré</b> — Je surveille les marchés...")
            else:
                logger.error(f"Telegram erreur getMe: {data}")
                self._enabled = False
        except Exception as e:
            logger.error(f"Telegram connexion échouée: {e}")
            self._enabled = False

    async def stop(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def send_message(self, text: str) -> bool:
        if not self._enabled:
            return False
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        try:
            url = TELEGRAM_BASE_URL.format(token=self._token, method="sendMessage")
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
            }
            async with self._session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    logger.warning(f"Telegram sendMessage failed: {data.get('description')}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Erreur envoi Telegram: {e}")
            return False

    async def notify_opportunity(self, signal: dict) -> None:
        direction_emoji = "🟢" if signal.get("direction") == "YES" else "🔴"
        confidence = signal.get("confidence", 0) * 100
        edge = signal.get("edge", 0) * 100
        market_price = signal.get("market_price", 0) * 100
        predicted_prob = signal.get("predicted_prob", 0) * 100
        market_url = signal.get("market_url", "")

        # Ligne LLM reasoning
        llm_line = ""
        if signal.get("llm_reasoning"):
            llm_line = f"\n🤖 <b>IA:</b> <i>{signal['llm_reasoning'][:160]}</i>"

        # Ligne Metaculus consensus
        meta_line = ""
        if signal.get("metaculus_prob") is not None:
            meta_prob = signal["metaculus_prob"] * 100
            meta_src = signal.get("metaculus_source", "Experts")
            meta_line = f"\n📐 <b>{meta_src}:</b> {meta_prob:.0f}% de probabilité"

        # Urgence si marché se résout bientôt
        urgency_line = ""
        urgency = signal.get("urgency_bonus", 0)
        if urgency >= 0.25:
            urgency_line = "\n⚡ <b>URGENT</b> — résolution dans <24h"
        elif urgency >= 0.15:
            urgency_line = "\n⏳ Résolution dans <48h"

        url_line = f'\n🔗 <a href="{market_url}">Voir sur Polymarket</a>' if market_url else ""

        msg = (
            f"🎯 <b>OPPORTUNITÉ DÉTECTÉE</b>\n\n"
            f"📊 <b>Marché:</b> {signal.get('question', 'N/A')[:80]}\n"
            f"{direction_emoji} <b>Direction:</b> {signal.get('direction', 'N/A')}\n"
            f"💰 <b>Prix marché:</b> {market_price:.1f}¢\n"
            f"🧠 <b>Prob. prédite:</b> {predicted_prob:.1f}¢\n"
            f"📈 <b>Edge:</b> {edge:+.1f}%\n"
            f"🎲 <b>Confiance:</b> {confidence:.1f}%\n"
            f"📡 <b>Source:</b> {signal.get('source', 'N/A')}"
            f"{meta_line}{llm_line}{urgency_line}{url_line}\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
        await self.send_message(msg)

    async def notify_trade_placed(self, trade: dict) -> None:
        direction_emoji = "🟢" if trade.get("direction") == "YES" else "🔴"
        msg = (
            f"✅ <b>TRADE PLACÉ</b>\n\n"
            f"📊 <b>Marché:</b> {trade.get('question', 'N/A')[:80]}\n"
            f"{direction_emoji} <b>Direction:</b> {trade.get('direction')}\n"
            f"💵 <b>Montant:</b> ${trade.get('size_usd', 0):.2f}\n"
            f"💰 <b>Prix entrée:</b> {trade.get('entry_price', 0) * 100:.1f}¢\n"
            f"🎲 <b>Confiance:</b> {trade.get('confidence', 0) * 100:.1f}%\n"
            f"🆔 Ordre: <code>{str(trade.get('order_id', 'N/A'))[:16]}...</code>\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
        await self.send_message(msg)

    async def notify_trade_result(self, trade: dict) -> None:
        won = trade.get("status") == "WON"
        emoji = "🏆" if won else "💀"
        pnl = trade.get("pnl", 0)
        pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"

        msg = (
            f"{emoji} <b>TRADE {'GAGNÉ' if won else 'PERDU'}</b>\n\n"
            f"📊 <b>Marché:</b> {trade.get('question', 'N/A')[:80]}\n"
            f"💵 <b>P&L:</b> <code>{pnl_str}</code>\n"
            f"📈 <b>Prix sortie:</b> {trade.get('exit_price', 0) * 100:.1f}¢\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
        await self.send_message(msg)

    async def notify_daily_report(self, stats: dict) -> None:
        win_rate = stats.get("win_rate", 0)
        total_pnl = stats.get("total_pnl", 0)
        pnl_str = f"+${total_pnl:.2f}" if total_pnl >= 0 else f"-${abs(total_pnl):.2f}"

        msg = (
            f"📊 <b>RAPPORT JOURNALIER</b>\n"
            f"═══════════════════\n"
            f"🏆 <b>Win rate:</b> {win_rate:.1f}%\n"
            f"💵 <b>P&amp;L total:</b> <code>{pnl_str}</code>\n"
            f"📈 <b>Total trades:</b> {stats.get('total', 0)}\n"
            f"✅ <b>Gagnés:</b> {stats.get('wins', 0)}\n"
            f"❌ <b>Perdus:</b> {stats.get('losses', 0)}\n"
            f"🎲 <b>Confiance moy.:</b> {stats.get('avg_confidence', 0) * 100:.1f}%\n"
            f"📊 <b>Edge moyen:</b> {stats.get('avg_edge', 0) * 100:.1f}%\n"
            f"═══════════════════\n"
            f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        await self.send_message(msg)

    async def notify_anomaly(self, market: dict) -> None:
        msg = (
            f"⚡ <b>ANOMALIE DÉTECTÉE</b>\n\n"
            f"📊 <b>Marché:</b> {market.get('question', 'N/A')[:80]}\n"
            f"📈 <b>Score anomalie:</b> {market.get('anomaly_score', 0):.2f}\n"
            f"💰 <b>Prix YES:</b> {market.get('yes_price', 0) * 100:.1f}¢\n"
            f"📊 <b>Spread:</b> {market.get('spread', 0) * 100:.1f}%\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
        await self.send_message(msg)

    async def notify_learning_update(self, pattern: str, action: str) -> None:
        msg = (
            f"🧠 <b>APPRENTISSAGE MIS À JOUR</b>\n\n"
            f"🔍 <b>Pattern détecté:</b> {pattern}\n"
            f"🔧 <b>Action corrective:</b> {action}\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
        await self.send_message(msg)

    async def notify_error(self, error: str, context: str = "") -> None:
        msg = (
            f"🚨 <b>ERREUR BOT</b>\n\n"
            f"📍 <b>Contexte:</b> {context}\n"
            f"❌ <b>Erreur:</b> <code>{error[:200]}</code>\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
        await self.send_message(msg)
