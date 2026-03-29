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

VALIDATION_PROMPT = """You are an expert prediction market trader on Polymarket. Analyze this signal concisely.

Market: {question}
Market price (YES): {yes_price:.0%}
Our model prediction: {predicted_prob:.0%}
Direction: {direction} | Edge: {edge:+.0%} | Confidence: {confidence:.0%}

Recent news ({n_texts} sources):
{news_summary}

Answer in JSON only (reason must be in French):
{{
  "valid": true or false,
  "adj": float between -0.15 and +0.15 (confidence adjustment),
  "prob": float 0.0-1.0 (your probability estimate for YES),
  "reason": "1-2 phrases en français expliquant l'opportunité ou le problème",
  "flags": ["list any red flags, empty if none"]
}}

Red flags to check: event already resolved, news irrelevant to market, direction contradicts news, market at extreme price for wrong reasons."""


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

            prompt = VALIDATION_PROMPT.format(
                question=signal.get("question", ""),
                yes_price=signal.get("market_price", 0.5),
                predicted_prob=signal.get("predicted_prob", 0.5),
                direction=signal.get("direction", "YES"),
                edge=signal.get("edge", 0),
                confidence=signal.get("confidence", 0.7),
                n_texts=signal.get("texts_count", 0),
                news_summary=news_summary,
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
            flags = result.get("flags", [])

            new_conf = min(max(signal.get("confidence", 0.7) + adj, 0.0), 1.0)

            signal["llm_valid"] = valid
            signal["llm_reasoning"] = reasoning
            signal["llm_prob"] = prob
            signal["llm_flags"] = flags
            signal["confidence"] = new_conf

            status = "✅ VALIDÉ" if valid else "❌ REJETÉ"
            logger.info(
                f"LLM {status}: {signal.get('question', '')[:55]} "
                f"| adj={adj:+.2f} | {reasoning[:70]}"
            )

        except Exception as e:
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
