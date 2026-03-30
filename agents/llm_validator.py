"""
PolyPoly — Agent 8 : Validation LLM (Claude)
Analyse experte de chaque signal AVANT trade.
Raisonnement fondamental — pas de moyenne de probabilités.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional
from loguru import logger

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from config import ANTHROPIC_API_KEY, LLM_MODEL


# ─────────────────────────────────────────────────────────────────────────────
# Persona d'expert adapté à la catégorie du marché
# ─────────────────────────────────────────────────────────────────────────────
_EXPERT_PERSONA = {
    "crypto": (
        "un trader crypto senior avec 10 ans d'expérience en prop trading. "
        "Tu analyses les cycles de marché, les catalyseurs macro (Fed, ETF, halving), "
        "et le sentiment on-chain. Tu sais quand les marchés crypto sur-réagissent "
        "ou sous-réagissent aux news."
    ),
    "politics_us": (
        "un analyste électoral américain de haut niveau (niveau Nate Silver / Larry Sabato). "
        "Tu connais les biais systématiques des sondages, les taux de base historiques, "
        "l'effet incumbency, et les dynamiques de retournement de dernière minute. "
        "Tu ne te fies jamais à un seul sondage."
    ),
    "geopolitics": (
        "un analyste géopolitique senior (niveau RAND Corporation / IISS). "
        "Tu évalues les conflits, accords, et dynamiques de pouvoir avec recul historique. "
        "Tu sais distinguer ce qui est du bruit médiatique de ce qui est structurellement significatif."
    ),
    "sports": (
        "un analyste sportif quantitatif (niveau FiveThirtyEight Sports). "
        "Tu analyses les statistiques récentes, les tendances de forme, "
        "les blessures, et les dynamiques domicile/extérieur. "
        "Tu sais que les marchés sportifs sont TRÈS efficients — un edge > 8% est rare."
    ),
    "economics": (
        "un économiste macro senior (ex-hedge fund macro global, 15 ans d'expérience). "
        "Tu analyses les données Fed, inflation, emploi, et leurs impacts sur les marchés. "
        "Tu comprends les décalages temporels entre les événements macro et leurs effets."
    ),
    "tech": (
        "un analyste tech senior (ex-VC top tier, 10 ans Silicon Valley). "
        "Tu comprends les cycles produit, les dynamiques concurrentielles, "
        "et les signaux faibles dans l'écosystème tech."
    ),
    "other": (
        "un trader professionnel de marchés de prédiction (Polymarket top 1%). "
        "Tu as vu des milliers de marchés se résoudre. Tu sais quand un edge est réel "
        "et quand c'est une illusion statistique."
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# Prompt principal
# ─────────────────────────────────────────────────────────────────────────────
VALIDATION_PROMPT = """Tu es {expert_persona}

Un algorithme vient de détecter une opportunité de trading sur Polymarket.
Ton rôle : DÉCIDER si cela vaut vraiment la peine d'investir. Comme si c'était ton propre argent.

══════════════════════════════════════════
OPPORTUNITÉ DÉTECTÉE
══════════════════════════════════════════
Question   : {question}
Catégorie  : {category}
Signal type: {signal_type}

Prix actuel YES : {yes_price:.1%}  → le marché dit qu'il y a {yes_pct:.0f}% de chance que OUI
Notre algo prédit: {predicted_prob:.1%}  → edge apparent de {edge:+.1%}
Volume 24h : ${volume_24h:,.0f}   |   Résolution dans : {time_to_resolution}
Confiance modèle : {confidence:.0%}

Sources analysées ({n_texts} articles) :
{news_summary}

══════════════════════════════════════════
TON ANALYSE D'EXPERT EN 5 POINTS
══════════════════════════════════════════

POINT 1 — POURQUOI LE MARCHÉ AURAIT TORT ?
Le marché dit {yes_pct:.0f}%. Si notre thèse est correcte, c'est que le marché sous-estime
ou surestime quelque chose. Qu'est-ce que les autres participants ont raté ou ignoré ?
(NE DIS PAS "les sources indiquent X%" — dis POURQUOI fondamentalement)

POINT 2 — LES VRAIS DRIVERS DE L'OUTCOME
Quels sont les 2-3 facteurs qui vont RÉELLEMENT déterminer si l'outcome est OUI ou NON ?
Pas les probabilités des autres sites. Les CAUSES fondamentales.

POINT 3 — LE SCÉNARIO PERDANT
Quel est le scénario le plus plausible où ce trade perd ? Quelle probabilité lui donnes-tu ?
Quels biais cognitifs dois-tu éviter ici ? (recency bias, narrative fallacy, etc.)

POINT 4 — LA VALEUR ESPÉRÉE RÉELLE
Edge apparent : {edge:+.1%}
Si le marché est efficient sur ce type de marché (volume ${volume_24h:,.0f}), un edge {edge:+.1%} est-il réel ou du bruit ?
Est-ce que l'asymétrie risque/récompense justifie vraiment d'y mettre ${capital:.0f} ?

POINT 5 — DÉCISION FINALE (c'est ton argent, pas celui d'un algo)
En tant qu'expert humain avec tous les éléments en main :
Tu parierais {direction} sur ce marché OUI ou NON — ou tu PASSES ?

══════════════════════════════════════════
RÉPONSE JSON UNIQUEMENT
══════════════════════════════════════════
{{
  "pourquoi_marche_tort": "1-2 phrases : l'avantage informationnel RÉEL ou 'Aucun avantage clair identifié'",
  "drivers_fondamentaux": "2-3 phrases : les vrais facteurs causaux",
  "scenario_perdant": "1-2 phrases : le scénario le plus plausible pour perdre",
  "ev_positif": true ou false,
  "verdict": "OUI" ou "NON" ou "PASSE",
  "conviction": 1 à 10,
  "consensus_pct": 0.0 à 1.0,
  "valid": true ou false,
  "adj": -0.20 à +0.20,
  "prob": 0.0 à 1.0,
  "reason": "2-3 phrases en français : ton verdict final comme un trader expert humain"
}}

RÈGLES NON NÉGOCIABLES :
- valid = false si conviction < 7
- valid = false si consensus_pct < 0.55
- valid = false si ev_positif = false
- valid = false si "pourquoi_marche_tort" dit 'Aucun avantage clair'
- valid = false si marché très efficient (volume > $200k ET edge < 0.08)
- valid = false si résolution dans < 2h (trop tard pour agir)
- Si tu n'as PAS de vraie thèse fondamentale → verdict = PASSE, valid = false
- Sois SÉVÈRE. Il vaut mieux rater une opportunité que perdre de l'argent."""


class LLMValidator:
    """
    Agent 8 — Validation LLM des signaux avec Claude.

    Pour chaque signal ≥65% confiance :
    - Analyse fondamentale (pas juste une moyenne de probabilités)
    - Expert adapté à la catégorie du marché
    - Rejet si conviction < 7/10 ou consensus < 55%
    - Enrichit le signal avec le raisonnement expert complet
    """

    CONVICTION_THRESHOLD = 7   # Conviction minimum pour valider un signal
    CONSENSUS_THRESHOLD = 0.55  # % d'experts qui voteraient dans le sens du signal

    def __init__(self):
        self._client = None
        self._enabled = bool(ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY)
        self._calls_this_hour = 0
        self._max_calls_per_hour = 50
        self._hour_reset_task: Optional[asyncio.Task] = None

    async def start(self):
        if not self._enabled:
            logger.warning("LLM Validator désactivé (clé Anthropic manquante)")
            return
        self._client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        self._hour_reset_task = asyncio.create_task(self._reset_counter_loop())
        logger.info("Agent 8 (LLM Validator / Expert Trader) connecté")

    async def _reset_counter_loop(self):
        """Réinitialise le compteur d'appels toutes les heures."""
        while True:
            await asyncio.sleep(3600)
            self._calls_this_hour = 0
            logger.debug("LLM Validator: compteur horaire réinitialisé")

    def _format_time_to_resolution(self, signal: dict) -> str:
        """Formate le temps restant avant résolution."""
        end_date = signal.get("end_date") or signal.get("market_end_date")
        if not end_date:
            urgency = signal.get("urgency_bonus", 0)
            if urgency >= 0.40:
                return "< 6 heures"
            elif urgency >= 0.25:
                return "< 24 heures"
            elif urgency >= 0.15:
                return "< 48 heures"
            return "inconnu"

        try:
            if isinstance(end_date, str):
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            else:
                end_dt = end_date
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            delta = end_dt - now
            total_hours = delta.total_seconds() / 3600
            if total_hours < 0:
                return "EXPIRÉ"
            elif total_hours < 2:
                return f"{int(total_hours * 60)} minutes"
            elif total_hours < 48:
                return f"{int(total_hours)} heures"
            else:
                return f"{int(total_hours / 24)} jours"
        except Exception:
            return "inconnu"

    async def validate(self, signal: dict, relevant_texts: list[str]) -> dict:
        """
        Analyse experte d'un signal avec Claude.
        Retourne le signal enrichi avec le raisonnement complet.
        """
        if not self._client:
            logger.debug("LLM Validator ignoré: client non initialisé")
            signal["llm_valid"] = True
            signal["llm_reasoning"] = ""
            return signal

        if self._calls_this_hour >= self._max_calls_per_hour:
            logger.warning(f"LLM Validator: limite horaire ({self._max_calls_per_hour}/h)")
            signal["llm_valid"] = True
            signal["llm_reasoning"] = ""
            return signal

        try:
            # Préparer le résumé des actualités
            news_summary = "\n".join(
                f"• {t[:200]}" for t in relevant_texts[:8]
            ) or "Aucune news récente trouvée pour ce marché."

            # Persona expert selon la catégorie
            category = signal.get("category", "other")
            expert_persona = _EXPERT_PERSONA.get(category, _EXPERT_PERSONA["other"])

            # Contexte temporel
            time_to_resolution = self._format_time_to_resolution(signal)

            # Volume 24h (depuis le signal ou 0)
            volume_24h = float(signal.get("volume_24h", 0) or 0)

            from config import CAPITAL_USD
            yes_price = signal.get("market_price", 0.5)
            edge = signal.get("edge", 0)

            prompt = VALIDATION_PROMPT.format(
                expert_persona=expert_persona,
                question=signal.get("question", ""),
                category=category,
                signal_type=signal.get("signal_type", "COMBINED"),
                yes_price=yes_price,
                yes_pct=yes_price * 100,
                predicted_prob=signal.get("predicted_prob", 0.5),
                edge=edge,
                volume_24h=volume_24h,
                time_to_resolution=time_to_resolution,
                confidence=signal.get("confidence", 0.7),
                n_texts=signal.get("texts_count", 0),
                news_summary=news_summary,
                direction=signal.get("direction", "YES"),
                capital=CAPITAL_USD,
            )

            response = await self._client.messages.create(
                model=LLM_MODEL,
                max_tokens=700,
                messages=[{"role": "user", "content": prompt}],
            )
            self._calls_this_hour += 1

            text = response.content[0].text.strip()

            # Extraire le JSON
            if "{" in text and "}" in text:
                json_str = text[text.index("{"):text.rindex("}") + 1]
                result = json.loads(json_str)
            else:
                logger.warning("LLM: pas de JSON dans la réponse")
                signal["llm_valid"] = True
                signal["llm_reasoning"] = ""
                return signal

            # ── Lecture des champs ───────────────────────────────────────
            valid         = bool(result.get("valid", True))
            adj           = float(result.get("adj", 0.0))
            prob          = float(result.get("prob", signal.get("predicted_prob", 0.5)))
            reasoning     = str(result.get("reason", "")).strip()
            conviction    = int(result.get("conviction", 5))
            consensus_pct = float(result.get("consensus_pct", 0.5))
            verdict       = str(result.get("verdict", "PASSE")).upper()
            ev_positif    = bool(result.get("ev_positif", True))
            pourquoi      = str(result.get("pourquoi_marche_tort", "")).strip()
            drivers       = str(result.get("drivers_fondamentaux", "")).strip()
            risque        = str(result.get("scenario_perdant", "")).strip()

            # ── Règles absolues ──────────────────────────────────────────
            if conviction < self.CONVICTION_THRESHOLD:
                valid = False
            if consensus_pct < self.CONSENSUS_THRESHOLD:
                valid = False
            if not ev_positif:
                valid = False
            if verdict == "PASSE":
                valid = False
            if time_to_resolution in ("EXPIRÉ", "< 2 heures"):
                valid = False

            # Marché très efficient : edge doit être plus grand
            if volume_24h > 200_000 and abs(edge) < 0.08:
                valid = False
                reasoning = (
                    f"Marché trop efficient (${volume_24h:,.0f} de volume) "
                    f"pour un edge de seulement {edge:+.1%}. " + reasoning
                )

            new_conf = min(max(signal.get("confidence", 0.7) + adj, 0.0), 1.0)

            # ── Enrichissement du signal ─────────────────────────────────
            signal["llm_valid"]      = valid
            signal["llm_reasoning"]  = reasoning
            signal["llm_prob"]       = prob
            signal["llm_conviction"] = conviction
            signal["llm_consensus"]  = consensus_pct
            signal["llm_verdict"]    = verdict
            signal["llm_ev"]         = ev_positif
            signal["llm_edge_info"]  = pourquoi
            signal["llm_drivers"]    = drivers
            signal["llm_risque"]     = risque
            # Rétro-compat avec anciens champs
            signal["llm_pour"]       = [pourquoi, drivers] if pourquoi else []
            signal["llm_contre"]     = [risque] if risque else []
            signal["llm_flags"]      = [risque] if risque else []
            signal["confidence"]     = new_conf

            status = "✅ VALIDÉ" if valid else "❌ REJETÉ"
            logger.info(
                f"LLM {status} [{verdict}]: {signal.get('question', '')[:55]} "
                f"| conviction={conviction}/10 | consensus={consensus_pct:.0%} "
                f"| EV={'✓' if ev_positif else '✗'} | {reasoning[:80]}"
            )

        except Exception as e:
            err_str = str(e)
            if "credit balance is too low" in err_str or "insufficient_credits" in err_str:
                logger.error(
                    "💳 ANTHROPIC: solde insuffisant — LLM Validator désactivé.\n"
                    "→ Recharge sur https://console.anthropic.com/settings/billing"
                )
                self._client = None
            else:
                logger.warning(f"LLM validation erreur: {e}")
            signal["llm_valid"] = True
            signal["llm_reasoning"] = ""

        return signal

    def reset_daily_counter(self):
        self._calls_this_hour = 0

    def stop(self):
        if self._hour_reset_task:
            self._hour_reset_task.cancel()
        logger.info("Agent 8 (LLM Validator) arrêté")
