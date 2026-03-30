"""
PolyPoly — Notifications Telegram
Utilise l'API HTTP Telegram directement (pas de python-telegram-bot).
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_BASE_URL = "https://api.telegram.org/bot{token}/{method}"


class TelegramNotifier:
    """Gestionnaire de notifications Telegram via HTTP direct."""

    # Cooldown anti-doublon : 2h par marché
    _NOTIF_COOLDOWN_HOURS = 2

    def __init__(self):
        self.chat_id = TELEGRAM_CHAT_ID
        self._token = TELEGRAM_BOT_TOKEN
        self._enabled = bool(self._token and self.chat_id)
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_notified: dict[str, datetime] = {}  # market_id → heure dernière alerte

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

    # Émojis par catégorie
    _CATEGORY_EMOJI = {
        "crypto": "₿", "sports": "⚽", "politics_us": "🇺🇸",
        "geopolitics": "🌍", "economics": "📉", "tech": "💻", "other": "🎯",
    }

    # Traductions direction
    _DIRECTION_FR = {"YES": "ACHETER OUI", "NO": "VENDRE NON"}

    # Traductions type de signal
    _TYPE_FR = {
        "ARBITRAGE": "Arbitrage inter-plateformes",
        "SENTIMENT": "Signal de sentiment",
        "ORDERBOOK": "Signal carnet d'ordres",
        "PREDICTION": "Prédiction ML",
        "WHALE": "Activité baleine",
        "COMBINED": "Signal combiné",
        "ANOMALY": "Anomalie de prix",
        "SMART_MONEY": "Smart Money / Gros traders",
        "BOOKMAKER": "Cotes bookmaker",
        "WIKI": "Signal Wikipedia",
        "COHERENCE": "Cohérence inter-marchés",
    }

    async def notify_opportunity(self, signal: dict) -> None:
        # ── Garde absolue : marché quasi-résolu → on ne notifie JAMAIS ──────
        market_price = float(signal.get("market_price", 0.5))
        if market_price < 0.15 or market_price > 0.85:
            logger.debug(
                f"notify_opportunity bloquée: prix {market_price:.1%} extrême "
                f"→ marché quasi-résolu ou terminé ({signal.get('question','')[:50]})"
            )
            return

        # Anti-doublon : ignorer si déjà notifié dans les 2 dernières heures
        market_id = str(signal.get("market_id", ""))
        now = datetime.now()
        last = self._last_notified.get(market_id)
        if last and (now - last) < timedelta(hours=self._NOTIF_COOLDOWN_HOURS):
            logger.debug(f"Doublon ignoré ({market_id}) — déjà notifié il y a {(now-last).seconds//60}min")
            return
        self._last_notified[market_id] = now

        direction = signal.get("direction", "YES")
        direction_emoji = "🟢" if direction == "YES" else "🔴"
        direction_fr = self._DIRECTION_FR.get(direction, direction)
        confidence = signal.get("confidence", 0) * 100
        edge = signal.get("edge", 0) * 100
        market_price = signal.get("market_price", 0) * 100
        predicted_prob = signal.get("predicted_prob", 0) * 100
        market_url = signal.get("market_url", "")
        category = signal.get("category", "other")
        cat_emoji = self._CATEGORY_EMOJI.get(category, "🎯")
        sig_type_fr = self._TYPE_FR.get(signal.get("signal_type", ""), "Signal IA")
        n_sources = signal.get("texts_count", 0)

        # ── Analyse experte IA — Soros/Silver/Renaissance ───────────────
        llm_reasoning  = signal.get("llm_reasoning", "").strip()
        conviction     = signal.get("llm_conviction", 0)
        consensus      = signal.get("llm_consensus", 0.0)
        verdict        = signal.get("llm_verdict", "")
        ev_ok          = signal.get("llm_ev", None)
        avantage       = signal.get("llm_edge_info", "").strip()
        base_rate      = signal.get("llm_base_rate", "").strip()
        premortem      = signal.get("llm_premortem", "").strip()
        reflexivite    = signal.get("llm_reflexivite", "").strip()
        contre_args    = signal.get("llm_contre", [])
        edge_struct    = signal.get("llm_edge_struct", None)

        if llm_reasoning or avantage:
            # ─ Ligne de verdict enrichie
            v_emoji = {"OUI": "✅", "NON": "❌", "PASSE": "⏸"}.get(verdict, "🔍")
            struct_icon = "🔁" if edge_struct else ("⚡" if edge_struct is False else "")
            verdict_line = (
                f"{v_emoji} <b>Verdict :</b> {verdict}"
                f"  |  🎯 Conviction <b>{conviction}/10</b>"
                f"  |  👥 Consensus <b>{consensus:.0%}</b>"
            )
            if ev_ok is not None:
                verdict_line += f"  |  {'📈' if ev_ok else '📉'} EV {'✓' if ev_ok else '✗'}"
            if edge_struct is not None:
                verdict_line += f"  |  {struct_icon} Edge {'structurel' if edge_struct else 'éphémère'}"
            verdict_line += "\n"

            # ─ Avantage informationnel (le plus important)
            avantage_line = f"💡 <b>Edge :</b> <i>{avantage[:180]}</i>\n" if avantage else ""

            # ─ Base rate Silver
            base_line = f"📊 <b>Base rate :</b> <i>{base_rate[:140]}</i>\n" if base_rate else ""

            # ─ Pré-mortem
            premortem_line = f"💀 <b>Si on perd :</b> <i>{premortem[:140]}</i>\n" if premortem else ""

            # ─ Conclusion
            reason_line = f"🤖 <i>{llm_reasoning[:200]}</i>\n" if llm_reasoning else ""

            opinion_block = (
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🧠 <b>ANALYSE EXPERT IA</b>\n"
                f"{verdict_line}"
                f"{avantage_line}"
                f"{base_line}"
                f"{premortem_line}"
                f"{reason_line}"
                f"\n"
            )
        else:
            # Avis minimal si LLM non disponible
            if abs(edge) >= 30:
                opinion_block = f"🤖 <b>Avis bot :</b>\n<i>Décalage très fort ({edge:+.0f}%) — opportunité rare.</i>\n\n"
            elif abs(edge) >= 15:
                opinion_block = f"🤖 <b>Avis bot :</b>\n<i>Décalage {edge:+.0f}% — prob. estimée {predicted_prob:.0f}% vs {market_price:.0f}% marché.</i>\n\n"
            else:
                opinion_block = ""

        # ── Validation externe (Metaculus / Manifold) ────────────────────
        external_line = ""
        if signal.get("metaculus_prob") is not None:
            meta_prob = signal["metaculus_prob"] * 100
            meta_src = signal.get("metaculus_source", "Experts")
            external_line = f"📐 <b>{meta_src} :</b> {meta_prob:.0f}% — <i>{'confirme' if abs(meta_prob - predicted_prob) < 10 else 'signale une divergence'}</i>\n"
        elif signal.get("cross_platform_prob") is not None:
            cp_prob = signal["cross_platform_prob"] * 100
            cp_src = signal.get("cross_platform_source", "Manifold")
            external_line = f"🔄 <b>{cp_src} :</b> {cp_prob:.0f}% de probabilité\n"

        # ── Urgence ──────────────────────────────────────────────────────
        urgency = signal.get("urgency_bonus", 0)
        if urgency >= 0.40:
            urgency_line = "⚡ <b>ULTRA-URGENT</b> — résolution dans moins de 6h\n"
        elif urgency >= 0.25:
            urgency_line = "⚡ <b>URGENT</b> — résolution dans moins de 24h\n"
        elif urgency >= 0.15:
            urgency_line = "⏳ Résolution dans moins de 48h\n"
        else:
            urgency_line = ""

        # ── Lien ─────────────────────────────────────────────────────────
        url_line = f'🔗 <a href="{market_url}"><b>Parier maintenant sur Polymarket →</b></a>' if market_url else ""

        # ── Barre de confiance visuelle ───────────────────────────────────
        filled = int(confidence / 10)
        conf_bar = "█" * filled + "░" * (10 - filled)

        msg = (
            f"{cat_emoji} <b>{sig_type_fr.upper()}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📌 <b>{signal.get('question', 'N/A')[:90]}</b>\n\n"
            f"{opinion_block}"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{direction_emoji} <b>{direction_fr}</b>\n"
            f"💰 Prix actuel : <b>{market_price:.1f}¢</b>   →   Prob. estimée : <b>{predicted_prob:.1f}%</b>\n"
            f"📈 Edge : <b>{edge:+.1f}%</b>\n"
            f"🎲 Confiance : <b>{confidence:.0f}%</b>  [{conf_bar}]\n"
            f"📡 Sources analysées : {n_sources}\n"
            f"{external_line}"
            f"{urgency_line}"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{url_line}\n"
            f"⏰ {now.strftime('%d/%m %H:%M')}"
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

    async def notify_news_flash(self, article: dict, market: dict) -> None:
        """Envoie une alerte info quand une news récente correspond à un marché actif."""
        title = article.get("title", "")[:120]
        source = article.get("source", "RSS")
        pub_date = article.get("pub_date")
        age_min = 0
        if pub_date:
            from datetime import timezone as _tz
            now = datetime.now(_tz.utc)
            age_min = int((now - pub_date).total_seconds() / 60)

        question = market.get("question", "")[:90]
        yes_price = market.get("yes_price", 0.5) * 100
        volume = market.get("volume_24h", 0)
        market_url = market.get("market_url", "")
        category = market.get("category", "other")
        cat_emoji = self._CATEGORY_EMOJI.get(category, "🎯")

        url_line = f'\n🔗 <a href="{market_url}">Voir le marché →</a>' if market_url else ""

        msg = (
            f"📰 <b>FLASH INFO {cat_emoji}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🗞 <b>{title}</b>\n"
            f"<i>Source : {source} — il y a {age_min} min</i>\n\n"
            f"📌 <b>Marché lié :</b> {question}\n"
            f"💰 Prix YES : <b>{yes_price:.1f}%</b>  |  Vol. 24h : <b>${volume:,.0f}</b>\n"
            f"{url_line}\n"
            f"⏰ {datetime.now().strftime('%d/%m %H:%M')}"
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
