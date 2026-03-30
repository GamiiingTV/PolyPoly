"""
PolyPoly — Agent 8 : Validation LLM (Claude)
Framework des meilleurs traders du monde : Soros + Silver + Renaissance + Kahneman.
Raisonnement fondamental, pas de moyennage de probabilités.
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
# Persona expert adapté à la catégorie
# ─────────────────────────────────────────────────────────────────────────────
_EXPERT_PERSONA = {
    "crypto": (
        "un trader crypto de niveau institutionnel (10+ ans, prop trading, ex-Alameda type). "
        "Tu comprends les cycles on-chain, les catalyseurs macro (Fed, ETF, halving), "
        "la psychologie des marchés crypto, et tu sais distinguer la spéculation du fondamental."
    ),
    "politics_us": (
        "un modélisateur électoral de niveau Nate Silver / Larry Sabato. "
        "Tu connais les biais systématiques des sondages, les taux de base historiques, "
        "l'effet incumbency, les dynamiques de base late swing, "
        "et tu ne te fies JAMAIS à un seul signal."
    ),
    "geopolitics": (
        "un analyste géopolitique de niveau RAND Corporation / IISS. "
        "Tu évalues les dynamiques de conflits et d'accords avec recul historique profond. "
        "Tu sépares le bruit médiatique des signaux structurels vrais."
    ),
    "sports": (
        "un analyste sportif quantitatif de niveau FiveThirtyEight / Two Hat. "
        "Tu sais que les marchés sportifs sont TRÈS efficients. "
        "Un edge >8% sur un marché sport est extrêmement rare — sois ultra-sceptique."
    ),
    "economics": (
        "un macro trader senior de hedge fund global (15+ ans). "
        "Tu analyses les dynamiques Fed, inflation, emploi avec une précision chirurgicale. "
        "Tu sais que les marchés économiques intègrent très vite les données publiques."
    ),
    "tech": (
        "un analyste tech senior (ex-VC tier-1, 10+ ans Silicon Valley). "
        "Tu comprends les cycles produit, les dynamiques concurrentielles, "
        "et les signaux faibles qui précèdent les retournements."
    ),
    "other": (
        "l'un des 10 meilleurs traders de marchés de prédiction au monde. "
        "Tu as résolu des milliers de marchés. Tu sais que l'edge est RARE. "
        "Tu refuses 90% des opportunités qui se présentent."
    ),
}

# Seuils d'edge requis selon l'efficience du marché
_EFFICIENCY_TIERS = [
    (500_000, 0.15, "Ultra-efficient"),
    (100_000, 0.10, "Très efficient"),
    (25_000,  0.07, "Efficient"),
    (5_000,   0.05, "Modérément efficient"),
    (0,       0.03, "Peu efficient"),
]


def _efficiency_label(volume: float, edge: float) -> tuple[str, bool]:
    """Retourne (description du tier, edge_suffisant)."""
    for threshold, required_edge, label in _EFFICIENCY_TIERS:
        if volume >= threshold:
            return label, abs(edge) >= required_edge
    return "Inconnu", True


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT PRINCIPAL — Framework élite
# ─────────────────────────────────────────────────────────────────────────────
VALIDATION_PROMPT = """Tu es {expert_persona}

Un algorithme vient de détecter ce qui ressemble à une opportunité de trading sur Polymarket.
TON RÔLE : décider si c'est une VRAIE opportunité ou une illusion statistique.
Les meilleurs traders du monde refusent 9 opportunités sur 10. Sois exigeant.

══════════════════════════════════════════
OPPORTUNITÉ
══════════════════════════════════════════
Question   : {question}
Catégorie  : {category}  |  Type signal : {signal_type}

Marché dit : {yes_pct:.0f}% de chance OUI  (prix {yes_price:.2f})
Algo prédit : {predicted_pct:.0f}%  →  Edge apparent : {edge:+.1%}
Volume 24h : ${volume_24h:,.0f}  ({efficiency_label})  |  Résolution : {time_to_resolution}

Seuil d'edge requis pour ce niveau de liquidité : {required_edge:.0%}
Edge suffisant ? {edge_ok}

Sources analysées ({n_texts} articles) :
{news_summary}

══════════════════════════════════════════
FRAMEWORK EN 7 QUESTIONS — RÉPONDS CHACUNE
══════════════════════════════════════════

① RÉFLEXIVITÉ (Soros)
"Qui a fixé ce prix à {yes_pct:.0f}% et POURQUOI auraient-ils tort ?
 S'agit-il de smart money ou de parieurs lambdas qui ont suivi une narrative ?"

② BASE RATE (Nate Silver)
"Pour ce TYPE d'événement dans le passé, quelle est la probabilité historique de base ?
 Ex : les incumbents gagnent 70% des re-elections. Les favoris sportifs gagnent X%.
 Après avoir posé cette base rate, les news actuelles la font-elles monter ou descendre ?"

③ EDGE STRUCTUREL (Renaissance Technologies)
"Est-ce que cet edge est structural — il se répéterait dans des situations similaires ?
 Ou est-ce un pattern aléatoire qui n'existera qu'une fois ?"

④ AVANTAGE INFORMATIONNEL
"En une phrase précise : quelle information exacte le marché n'a-t-il PAS intégrée ?
 Si tu ne peux pas répondre avec précision → il n'y a PAS d'edge, réponds 'Aucun identifié'."

⑤ PRÉ-MORTEM (Kahneman)
"Dans 30 jours, ce trade a perdu. Raconte le scénario qui s'est produit.
 Quelle probabilité donnes-tu à ce scénario perdant ?"

⑥ AVOCAT DU DIABLE (obligatoire)
"Donne les 2 arguments les plus solides CONTRE ce trade.
 Sois impitoyable — cherche les failles, les biais, les angles morts."

⑦ DÉCISION FINALE — ${capital:.0f}$ de ta poche
"En tenant compte de TOUT ce qui précède : est-ce que TOI, avec ta propre expertise,
 tu placerais ce trade avec ${capital:.0f}$ de ton argent réel ?
 OUI = je parie | NON = signal invalide | PASSE = pas assez clair pour agir"

══════════════════════════════════════════
JSON UNIQUEMENT — ZÉRO TEXTE HORS DU JSON
══════════════════════════════════════════
{{
  "reflexivite": "Qui a fixé le prix et pourquoi auraient-ils tort (ou pas)",
  "base_rate": "Base rate historique = X%, mise à jour avec les news = Y%",
  "edge_structurel": true ou false,
  "avantage_info": "L'information précise que le marché n'a pas, ou 'Aucun identifié'",
  "premortem": "Scénario perdant + sa probabilité estimée",
  "contre_arguments": ["argument 1", "argument 2"],
  "ev_positif": true ou false,
  "verdict": "OUI" ou "NON" ou "PASSE",
  "conviction": 1 à 10,
  "consensus_pct": 0.0 à 1.0,
  "valid": true ou false,
  "adj": -0.20 à +0.20,
  "prob": 0.0 à 1.0,
  "reason": "2-3 phrases : ton verdict final comme le meilleur trader du monde"
}}

RÈGLES ABSOLUES (si une seule est violée → valid = false) :
• conviction < 7 → valid = false
• consensus_pct < 0.55 → valid = false
• edge_structurel = false ET volume > $50k → valid = false
• avantage_info = 'Aucun identifié' → valid = false, verdict = PASSE
• ev_positif = false → valid = false
• edge insuffisant pour le tier de liquidité → valid = false
• résolution < 2h → valid = false (trop tard pour agir)
• PASSE est TOUJOURS préférable à NON si tu n'as pas de thèse solide
• Conviction 8+ = thèse fondamentale béton seulement"""


class LLMValidator:
    """
    Agent 8 — Analyse experte de chaque signal avec le framework des meilleurs traders.

    Framework : Soros (réflexivité) + Silver (base rates) +
                Renaissance (edge structurel) + Kahneman (pré-mortem)

    Seuils : conviction ≥ 7/10, consensus ≥ 55%, edge adapté à l'efficience du marché.
    """

    CONVICTION_THRESHOLD = 7
    CONSENSUS_THRESHOLD  = 0.55

    def __init__(self):
        self._client = None
        self._enabled = bool(ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY)
        self._calls_this_hour = 0
        self._max_calls_per_hour = 50
        self._hour_reset_task: Optional[asyncio.Task] = None
        # Suivi de calibration en mémoire
        self._predictions: list[dict] = []   # {prob, outcome, timestamp}
        self._calibration_score: float = 1.0  # 1.0 = parfaitement calibré

    async def start(self):
        if not self._enabled:
            logger.warning("LLM Validator désactivé (clé Anthropic manquante)")
            return
        self._client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        self._hour_reset_task = asyncio.create_task(self._reset_counter_loop())
        logger.info("Agent 8 (LLM Expert Trader — Soros/Silver/Renaissance) connecté")

    async def _reset_counter_loop(self):
        while True:
            await asyncio.sleep(3600)
            self._calls_this_hour = 0
            logger.debug("LLM Validator: compteur horaire réinitialisé")

    def _format_time_to_resolution(self, signal: dict) -> str:
        end_date = signal.get("end_date") or signal.get("market_end_date")
        if not end_date:
            urgency = signal.get("urgency_bonus", 0)
            if urgency >= 0.40: return "< 6 heures ⚠️"
            elif urgency >= 0.25: return "< 24 heures"
            elif urgency >= 0.15: return "< 48 heures"
            return "inconnu"
        try:
            if isinstance(end_date, str):
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            else:
                end_dt = end_date
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
            delta = end_dt - datetime.now(timezone.utc)
            hours = delta.total_seconds() / 3600
            if hours < 0:   return "EXPIRÉ ⛔"
            elif hours < 2: return f"{int(hours*60)} min ⚠️"
            elif hours < 48: return f"{int(hours)}h"
            else:            return f"{int(hours/24)} jours"
        except Exception:
            return "inconnu"

    def record_outcome(self, predicted_prob: float, outcome: bool):
        """Enregistre un résultat pour suivre la calibration."""
        self._predictions.append({
            "prob": predicted_prob,
            "outcome": 1 if outcome else 0,
            "ts": datetime.now(timezone.utc).timestamp(),
        })
        # Garder les 200 dernières prédictions
        self._predictions = self._predictions[-200:]
        self._update_calibration()

    def _update_calibration(self):
        """
        Calcule le score de calibration (Brier score).
        1.0 = parfait, 0.0 = catastrophique.
        """
        if len(self._predictions) < 10:
            return
        brier = sum(
            (p["prob"] - p["outcome"]) ** 2
            for p in self._predictions
        ) / len(self._predictions)
        # Brier 0.25 = random, 0.0 = parfait → score 0→1
        self._calibration_score = max(0.0, 1.0 - brier / 0.25)
        logger.info(f"LLM Calibration: {self._calibration_score:.2f} (Brier={brier:.3f}, n={len(self._predictions)})")

    async def validate(self, signal: dict, relevant_texts: list[str]) -> dict:
        """
        Analyse experte d'un signal.
        Retourne le signal enrichi avec le raisonnement complet.
        """
        if not self._client:
            signal["llm_valid"] = True
            signal["llm_reasoning"] = ""
            return signal

        if self._calls_this_hour >= self._max_calls_per_hour:
            logger.warning(f"LLM Validator: limite horaire ({self._max_calls_per_hour}/h)")
            signal["llm_valid"] = True
            signal["llm_reasoning"] = ""
            return signal

        try:
            # Préparer les actualités
            news_summary = "\n".join(
                f"• {t[:220]}" for t in relevant_texts[:8]
            ) or "Aucune news récente disponible pour ce marché."

            # Persona expert
            category = signal.get("category", "other")
            expert_persona = _EXPERT_PERSONA.get(category, _EXPERT_PERSONA["other"])

            # Contexte temporel
            time_to_resolution = self._format_time_to_resolution(signal)

            # Efficience du marché
            volume_24h = float(signal.get("volume_24h", 0) or 0)
            edge = signal.get("edge", 0)
            eff_label, edge_ok = _efficiency_label(volume_24h, edge)
            # Trouver l'edge requis
            required_edge = 0.03
            for threshold, req, _ in _EFFICIENCY_TIERS:
                if volume_24h >= threshold:
                    required_edge = req
                    break

            from config import CAPITAL_USD
            yes_price = float(signal.get("market_price", 0.5))

            prompt = VALIDATION_PROMPT.format(
                expert_persona=expert_persona,
                question=signal.get("question", ""),
                category=category,
                signal_type=signal.get("signal_type", "COMBINED"),
                yes_price=yes_price,
                yes_pct=yes_price * 100,
                predicted_pct=signal.get("predicted_prob", 0.5) * 100,
                edge=edge,
                volume_24h=volume_24h,
                efficiency_label=eff_label,
                required_edge=required_edge,
                edge_ok="✅ OUI" if edge_ok else "❌ NON — edge insuffisant pour ce marché",
                time_to_resolution=time_to_resolution,
                n_texts=signal.get("texts_count", 0),
                news_summary=news_summary,
                capital=CAPITAL_USD,
            )

            response = await self._client.messages.create(
                model=LLM_MODEL,
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
            )
            self._calls_this_hour += 1

            text = response.content[0].text.strip()
            if "{" not in text or "}" not in text:
                logger.warning("LLM: pas de JSON dans la réponse")
                signal["llm_valid"] = True
                signal["llm_reasoning"] = ""
                return signal

            json_str = text[text.index("{"):text.rindex("}") + 1]
            result = json.loads(json_str)

            # ── Extraction ────────────────────────────────────────────────
            valid         = bool(result.get("valid", True))
            adj           = float(result.get("adj", 0.0))
            prob          = float(result.get("prob", signal.get("predicted_prob", 0.5)))
            reasoning     = str(result.get("reason", "")).strip()
            conviction    = int(result.get("conviction", 5))
            consensus_pct = float(result.get("consensus_pct", 0.5))
            verdict       = str(result.get("verdict", "PASSE")).upper()
            ev_positif    = bool(result.get("ev_positif", True))
            edge_struct   = bool(result.get("edge_structurel", False))
            avantage      = str(result.get("avantage_info", "")).strip()
            premortem     = str(result.get("premortem", "")).strip()
            reflexivite   = str(result.get("reflexivite", "")).strip()
            base_rate     = str(result.get("base_rate", "")).strip()
            contre_args   = result.get("contre_arguments", [])

            # ── Règles absolues ───────────────────────────────────────────
            reject_reasons = []

            if conviction < self.CONVICTION_THRESHOLD:
                valid = False
                reject_reasons.append(f"conviction {conviction}/10 < {self.CONVICTION_THRESHOLD}")

            if consensus_pct < self.CONSENSUS_THRESHOLD:
                valid = False
                reject_reasons.append(f"consensus {consensus_pct:.0%} < {self.CONSENSUS_THRESHOLD:.0%}")

            if not ev_positif:
                valid = False
                reject_reasons.append("EV négative")

            if verdict == "PASSE":
                valid = False
                reject_reasons.append("verdict PASSE")

            if "Aucun identifié" in avantage or not avantage:
                valid = False
                reject_reasons.append("aucun avantage informationnel identifié")

            if not edge_ok:
                valid = False
                reject_reasons.append(
                    f"edge {abs(edge):.1%} insuffisant pour marché {eff_label} (requis {required_edge:.0%})"
                )

            if not edge_struct and volume_24h > 50_000:
                valid = False
                reject_reasons.append("edge non structurel sur marché efficient")

            if "EXPIRÉ" in time_to_resolution or "min ⚠️" in time_to_resolution:
                valid = False
                reject_reasons.append("résolution imminente")

            # Ajustement calibration : si le bot est sur-confiant, on réduit
            if self._calibration_score < 0.6:
                adj = min(adj, -0.05)
                logger.warning(f"LLM sous-calibré ({self._calibration_score:.2f}) — ajustement négatif")

            new_conf = min(max(signal.get("confidence", 0.7) + adj, 0.0), 1.0)

            # ── Enrichissement ────────────────────────────────────────────
            signal["llm_valid"]       = valid
            signal["llm_reasoning"]   = reasoning
            signal["llm_prob"]        = prob
            signal["llm_conviction"]  = conviction
            signal["llm_consensus"]   = consensus_pct
            signal["llm_verdict"]     = verdict
            signal["llm_ev"]          = ev_positif
            signal["llm_edge_info"]   = avantage
            signal["llm_reflexivite"] = reflexivite
            signal["llm_base_rate"]   = base_rate
            signal["llm_premortem"]   = premortem
            signal["llm_edge_struct"] = edge_struct
            signal["llm_contre"]      = contre_args
            # Rétro-compat
            signal["llm_pour"]        = [avantage, base_rate] if avantage else []
            signal["llm_flags"]       = contre_args
            signal["confidence"]      = new_conf

            status = "✅ VALIDÉ" if valid else "❌ REJETÉ"
            reject_str = f" [{', '.join(reject_reasons[:2])}]" if reject_reasons else ""
            logger.info(
                f"LLM {status}{reject_str}: {signal.get('question','')[:55]} "
                f"| conviction={conviction}/10 | consensus={consensus_pct:.0%} "
                f"| EV={'✓' if ev_positif else '✗'} | {eff_label}"
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
