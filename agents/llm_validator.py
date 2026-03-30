"""
PolyPoly — Agent 8 : Validation LLM (Claude)
Valide chaque signal avec un raisonnement causal avant de l'envoyer.
Élimine les faux positifs et enrichit les alertes avec une explication.
"""

import asyncio
import json
from typing import Optional
from loguru import logger

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from config import ANTHROPIC_API_KEY, LLM_MODEL

VALIDATION_PROMPT = """Tu es un trader expert sur Polymarket. Décide si ce signal vaut la peine d'être joué.

═══ SIGNAL ═══
Marché : {question}
Prix YES actuel : {yes_price:.0%}  |  Modèle prédit : {predicted_prob:.0%}
Direction : {direction}  |  Edge : {edge:+.0%}  |  Confiance modèle : {confidence:.0%}

═══ ACTUALITÉS ({n_texts} sources) ═══
{news_summary}

═══ ANALYSE EN 4 ÉTAPES ═══

1. ARGUMENTS POUR parier {direction} (basés sur les news ci-dessus)
2. AVOCAT DU DIABLE — pourquoi NE PAS parier (sois sévère, cherche les pièges)
3. CONSENSUS — sur 10 analystes qui voient ces mêmes news, combien voteraient {direction} ?
4. TU ES L'INVESTISSEUR — tu as ${capital:.0f} en jeu. C'est ton argent. Tu parierais OUI ou NON ?

Réponds en JSON uniquement (pas de texte hors du JSON) :
{{
  "pour": ["argument 1", "argument 2"],
  "contre": ["contre-argument 1", "contre-argument 2"],
  "consensus_pct": 0.0,
  "verdict": "OUI" ou "NON" ou "ABSTAIN",
  "certitude": 1,
  "valid": true,
  "adj": 0.0,
  "prob": 0.5,
  "reason": "1-2 phrases en français résumant ton verdict final"
}}

Règles :
- consensus_pct : fraction 0.0→1.0 des analystes qui voteraient dans le sens du signal
- certitude : 1 (zéro confiance) à 10 (quasi-certain)
- valid doit être FALSE si : certitude < 6, consensus_pct < 0.55, événement déjà résolu, news contredisent le signal
- adj : ajustement de confiance entre -0.15 et +0.15
- prob : ta propre estimation de probabilité YES (0.0 à 1.0)"""


class LLMValidator:
    """
    Agent 8 — Validation LLM des signaux avec Claude.

    Pour chaque signal ≥65% confiance :
    - Envoie la question + articles à Claude
    - Claude détecte les faux positifs (course déjà terminée, news hors sujet...)
    - Ajuste la confiance et génère une explication lisible
    """

    def __init__(self):
        self._client = None
        self._enabled = bool(ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY)
        self._calls_this_hour = 0
        self._max_calls_per_hour = 50  # Rate limit self-imposé
        self._hour_reset_task: Optional[asyncio.Task] = None

    async def start(self):
        if not self._enabled:
            logger.warning("LLM Validator désactivé (clé Anthropic manquante)")
            return
        self._client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        self._hour_reset_task = asyncio.create_task(self._reset_counter_loop())
        logger.info("Agent 8 (LLM Validator) connecté")

    async def _reset_counter_loop(self):
        """Réinitialise le compteur d'appels toutes les heures."""
        while True:
            await asyncio.sleep(3600)
            self._calls_this_hour = 0
            logger.debug("LLM Validator: compteur horaire réinitialisé")

    async def validate(self, signal: dict, relevant_texts: list[str]) -> dict:
        """
        Valide un signal avec Claude.
        Retourne le signal enrichi (llm_valid, llm_reasoning, confiance ajustée).
        """
        if not self._client:
            logger.debug("LLM Validator ignoré: client non initialisé")
            signal["llm_valid"] = True
            signal["llm_reasoning"] = ""
            return signal
        if self._calls_this_hour >= self._max_calls_per_hour:
            logger.warning(f"LLM Validator: limite horaire atteinte ({self._max_calls_per_hour} appels)")
            signal["llm_valid"] = True
            signal["llm_reasoning"] = ""
            return signal

        try:
            news_summary = "\n".join(
                f"• {t[:180]}" for t in relevant_texts[:6]
            ) or "No news found."

            from config import CAPITAL_USD
            prompt = VALIDATION_PROMPT.format(
                question=signal.get("question", ""),
                yes_price=signal.get("market_price", 0.5),
                predicted_prob=signal.get("predicted_prob", 0.5),
                direction=signal.get("direction", "YES"),
                edge=signal.get("edge", 0),
                confidence=signal.get("confidence", 0.7),
                n_texts=signal.get("texts_count", 0),
                news_summary=news_summary,
                capital=CAPITAL_USD,
            )

            response = await self._client.messages.create(
                model=LLM_MODEL,
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            self._calls_this_hour += 1

            text = response.content[0].text.strip()
            # Extraire le JSON
            if "{" in text:
                json_str = text[text.index("{"):text.rindex("}") + 1]
                result = json.loads(json_str)
            else:
                signal["llm_valid"] = True
                signal["llm_reasoning"] = ""
                return signal

            valid = bool(result.get("valid", True))
            adj = float(result.get("adj", 0.0))
            prob = float(result.get("prob", signal.get("predicted_prob", 0.5)))
            reasoning = str(result.get("reason", ""))
            certitude = int(result.get("certitude", 5))
            consensus_pct = float(result.get("consensus_pct", 0.5))
            verdict = str(result.get("verdict", "ABSTAIN"))
            pour = result.get("pour", [])
            contre = result.get("contre", [])

            # Forcer valid=False si certitude trop basse ou consensus insuffisant
            if certitude < 6 or consensus_pct < 0.55:
                valid = False

            new_conf = min(max(signal.get("confidence", 0.7) + adj, 0.0), 1.0)

            signal["llm_valid"] = valid
            signal["llm_reasoning"] = reasoning
            signal["llm_prob"] = prob
            signal["llm_flags"] = contre  # contre-arguments comme flags
            signal["llm_certitude"] = certitude
            signal["llm_consensus"] = consensus_pct
            signal["llm_verdict"] = verdict
            signal["llm_pour"] = pour
            signal["llm_contre"] = contre
            signal["confidence"] = new_conf

            status = "✅ VALIDÉ" if valid else "❌ REJETÉ"
            logger.info(
                f"LLM {status}: {signal.get('question', '')[:55]} "
                f"| certitude={certitude}/10 | consensus={consensus_pct:.0%} | {reasoning[:70]}"
            )

        except Exception as e:
            err_str = str(e)
            if "credit balance is too low" in err_str or "insufficient_credits" in err_str:
                # Désactiver le LLM jusqu'au prochain redémarrage pour éviter le spam
                logger.error(
                    "💳 ANTHROPIC: solde insuffisant — LLM Validator désactivé.\n"
                    "→ Recharge sur https://console.anthropic.com/settings/billing"
                )
                self._client = None  # Désactive proprement
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
