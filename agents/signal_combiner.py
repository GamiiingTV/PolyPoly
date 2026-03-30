"""
PolyPoly — Signal Meta-Combiner (Fusion Bayésienne)
Combine intelligemment les signaux de tous les agents.
Apprend quels agents sont fiables par catégorie de marché.
"""

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from utils.database import Database
try:
    from utils.telegram_bot import TelegramNotifier
except BaseException:
    TelegramNotifier = object  # type: ignore


# Poids initiaux par type de signal (ajustés dynamiquement)
DEFAULT_WEIGHTS = {
    "PREDICTION": 0.45,    # XGBoost + LLM — le plus fiable
    "ORDERBOOK":  0.30,    # Microstructure — alpha court terme
    "SENTIMENT":  0.15,    # Sentiment — utile mais bruité
    "ANOMALY":    0.10,    # Scanner anomalie — signal faible seul
    "ARBITRAGE":  1.00,    # Arbitrage — signal indépendant, pas combiné
}

# Seuil pour déclencher un trade combiné (abaissé car XGBoost en cours de formation)
COMBINED_SIGNAL_THRESHOLD = 0.68
# Bonus de confiance si 2+ signaux concordants
CONCORDANCE_BONUS = 0.05
# Bonus si 3+ signaux concordants
TRIPLE_CONCORDANCE_BONUS = 0.10


class CombinedSignal:
    """Signal fusionné de plusieurs sources."""

    def __init__(self, market_id: str, question: str,
                 direction: str, combined_confidence: float,
                 combined_edge: float, sources: list[dict]):
        self.market_id = market_id
        self.question = question
        self.direction = direction
        self.combined_confidence = combined_confidence
        self.combined_edge = combined_edge
        self.sources = sources
        self.created_at = datetime.now()

    @property
    def source_count(self) -> int:
        return len(self.sources)

    @property
    def source_types(self) -> list[str]:
        return [s.get("signal_type", "?") for s in self.sources]


class SignalCombiner:
    """
    Meta-combiner de signaux.

    Mécanisme :
    1. Récupère tous les signaux récents (<30min) par marché
    2. Groupe par direction (YES/NO)
    3. Applique une fusion Bayésienne pondérée
    4. Génère un signal combiné si la confiance dépasse le seuil
    5. Apprend quels agents sont les plus précis par catégorie
    """

    def __init__(self, db: Database, telegram: TelegramNotifier):
        self.db = db
        self.telegram = telegram
        # Performances par type d'agent : signal_type → {wins, total}
        self._agent_perf: dict[str, dict] = defaultdict(lambda: {"wins": 0, "total": 0})
        # Performances par catégorie : category → {wins, total}
        self._category_perf: dict[str, dict] = defaultdict(lambda: {"wins": 0, "total": 0})
        self._dynamic_weights = dict(DEFAULT_WEIGHTS)
        self._last_weight_update = datetime.now()

    async def combine_signals(self, market_id: str, market: dict) -> Optional[CombinedSignal]:
        """
        Fusionne tous les signaux récents pour un marché.
        Retourne un CombinedSignal si le seuil est atteint.
        """
        # Récupérer les signaux récents (30 dernières minutes)
        recent_signals = await self._get_recent_signals_for_market(market_id)
        if not recent_signals:
            return None

        # Séparer par direction
        yes_signals = [s for s in recent_signals if s.get("direction") == "YES"]
        no_signals  = [s for s in recent_signals if s.get("direction") == "NO"]

        # Choisir la direction majoritaire
        yes_weight = sum(self._get_signal_weight(s) * s.get("confidence", 0) for s in yes_signals)
        no_weight  = sum(self._get_signal_weight(s) * s.get("confidence", 0) for s in no_signals)

        if yes_weight == 0 and no_weight == 0:
            return None

        if yes_weight > no_weight:
            dominant_signals = yes_signals
            direction = "YES"
            dominant_weight = yes_weight
            opposite_weight = no_weight
        else:
            dominant_signals = no_signals
            direction = "NO"
            dominant_weight = no_weight
            opposite_weight = yes_weight

        # Méthode Bayésienne : P(correct | signaux) ∝ ∏ P(signal | correct)
        combined_confidence = self._bayesian_fusion(dominant_signals, direction)

        # Pénaliser si signaux contradictoires
        if opposite_weight > dominant_weight * 0.5:
            contradiction_penalty = (opposite_weight / dominant_weight) * 0.08
            combined_confidence = max(combined_confidence - contradiction_penalty, 0.5)

        # Bonus de concordance (plusieurs agents d'accord = plus fiable)
        n_agreeing = len(dominant_signals)
        if n_agreeing >= 3:
            combined_confidence = min(combined_confidence + TRIPLE_CONCORDANCE_BONUS, 0.95)
        elif n_agreeing >= 2:
            combined_confidence = min(combined_confidence + CONCORDANCE_BONUS, 0.92)

        if combined_confidence < COMBINED_SIGNAL_THRESHOLD:
            return None

        # Edge moyen pondéré
        total_w = sum(self._get_signal_weight(s) for s in dominant_signals)
        combined_edge = (
            sum(self._get_signal_weight(s) * abs(s.get("edge", 0))
                for s in dominant_signals) / total_w
            if total_w > 0 else 0
        )

        signal = CombinedSignal(
            market_id=market_id,
            question=market.get("question", ""),
            direction=direction,
            combined_confidence=round(combined_confidence, 4),
            combined_edge=round(combined_edge, 4),
            sources=dominant_signals,
        )

        logger.info(
            f"Signal combiné [{combined_confidence:.2%}]: {direction} "
            f"{market['question'][:50]} | Sources: {signal.source_types}"
        )

        # Notif si très haute confiance
        if combined_confidence > 0.82:
            await self.telegram.notify_opportunity({
                "question": market.get("question"),
                "direction": direction,
                "confidence": combined_confidence,
                "edge": combined_edge,
                "predicted_prob": market.get("yes_price", 0.5) + combined_edge,
                "market_price": market.get("yes_price", 0.5),
                "sentiment_score": 0.0,
                "source": f"COMBINED ({'+'.join(signal.source_types)})",
            })

        return signal

    def _bayesian_fusion(self, signals: list[dict], direction: str) -> float:
        """
        Fusion Bayésienne des probabilités de confiance.
        Traite chaque signal comme une évidence indépendante.
        P(correct) = 1 - ∏(1 - P_i × weight_i)
        """
        if not signals:
            return 0.5

        # Prior = 0.5 (incertitude totale)
        log_odds = 0.0

        import math
        for sig in signals:
            p = sig.get("confidence", 0.5)
            w = self._get_signal_weight(sig)

            # Odds ratio pour ce signal
            p_adjusted = 0.5 + (p - 0.5) * w
            p_adjusted = max(0.501, min(0.999, p_adjusted))

            log_odds += math.log(p_adjusted / (1 - p_adjusted))

        # Convertir log-odds en probabilité
        prob = 1 / (1 + math.exp(-log_odds))
        return min(max(prob, 0.5), 0.95)

    def _get_signal_weight(self, signal: dict) -> float:
        """Retourne le poids dynamique d'un signal selon son type."""
        signal_type = signal.get("signal_type", "PREDICTION")
        return self._dynamic_weights.get(signal_type, 0.3)

    async def _get_recent_signals_for_market(
        self, market_id: str, minutes: int = 30
    ) -> list[dict]:
        """Récupère les signaux récents pour un marché donné."""
        all_signals = await self.db.get_recent_signals(limit=200)
        cutoff = datetime.now() - timedelta(minutes=minutes)

        result = []
        for sig in all_signals:
            if sig.get("market_id") != market_id:
                continue
            # Vérifier la fraîcheur
            created_str = sig.get("created_at", "")
            if created_str:
                try:
                    created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                    if created.replace(tzinfo=None) < cutoff:
                        continue
                except Exception:
                    pass
            result.append(sig)

        return result

    async def update_agent_performance(self, trade: dict) -> None:
        """
        Met à jour les performances des agents basé sur un trade résolu.
        Permet d'ajuster dynamiquement les poids.
        """
        signal_id = trade.get("signal_id")
        if not signal_id:
            return

        # Retrouver le type du signal
        signals = await self.db.get_recent_signals(limit=500)
        source_signal = next(
            (s for s in signals if s.get("id") == signal_id), None
        )
        if not source_signal:
            return

        signal_type = source_signal.get("signal_type", "PREDICTION")
        won = trade.get("status") == "WON"

        self._agent_perf[signal_type]["total"] += 1
        if won:
            self._agent_perf[signal_type]["wins"] += 1

        # Recalculer les poids si assez de données
        await self._maybe_update_weights()

    async def _maybe_update_weights(self) -> None:
        """Recalcule les poids dynamiquement basé sur les performances réelles."""
        # Mettre à jour toutes les heures max
        if datetime.now() - self._last_weight_update < timedelta(hours=1):
            return

        MIN_SAMPLES = 10
        new_weights = dict(DEFAULT_WEIGHTS)

        for signal_type, perf in self._agent_perf.items():
            if perf["total"] < MIN_SAMPLES:
                continue
            win_rate = perf["wins"] / perf["total"]
            # Poids proportionnel au win rate, borné entre 0.05 et 0.95
            new_weights[signal_type] = min(max(win_rate, 0.05), 0.95)

        # Normaliser (sauf ARBITRAGE qui reste à 1.0)
        regular = {k: v for k, v in new_weights.items() if k != "ARBITRAGE"}
        total = sum(regular.values())
        if total > 0:
            for k in regular:
                new_weights[k] = regular[k] / total

        self._dynamic_weights = new_weights
        self._last_weight_update = datetime.now()

        logger.info(f"Poids mis à jour: {new_weights}")
        await self.db.set_param("signal_weights", new_weights, "Performance update")

    async def detect_coherence_signals(self) -> list[dict]:
        """
        Détecte les incohérences logiques entre marchés liés.

        Exemple : Si "Trump win" est à 60% et "Biden win" est à 55%
        → leur somme = 115% > 100% → l'un des deux est sur-évalué.
        → Signal SHORT sur le plus surévalué.

        Exemple 2 : "Republicans win Senate" à 65% mais
        "Trump win Presidency" à 40% → contradiction politique → signal.
        """
        import re as _re
        markets = await self.db.get_active_markets(limit=200)
        signals = []

        # Grouper les marchés par topic (mots-clés communs)
        stop = {"will", "the", "a", "an", "in", "on", "at", "to", "win", "be"}
        grouped: dict[str, list[dict]] = {}

        for m in markets:
            # Ignorer les marchés quasi-résolus (prix déjà extrême)
            yes_p = m.get("yes_price", 0.5)
            if yes_p < 0.09 or yes_p > 0.91:
                continue
            q = m.get("question", "")
            words = [w.lower() for w in _re.findall(r'\b\w{4,}\b', q) if w.lower() not in stop][:3]
            if len(words) < 2:
                continue
            key = " ".join(sorted(words[:2]))
            grouped.setdefault(key, []).append(m)

        for key, group in grouped.items():
            if len(group) < 2:
                continue

            # Détecter les paires mutuellement exclusives (YES A + YES B > 1.0)
            for i, m1 in enumerate(group):
                for m2 in group[i+1:]:
                    p1 = m1.get("yes_price", 0.5)
                    p2 = m2.get("yes_price", 0.5)

                    # Incohérence : somme > 1.10 (l'un est clairement surévalué)
                    if p1 + p2 > 1.10:
                        # Shorter le plus surévalué (prix le plus haut)
                        overvalued = m1 if p1 > p2 else m2
                        overval_price = max(p1, p2)
                        fair_price = 1.0 - min(p1, p2)  # Si l'autre est correct
                        edge = fair_price - overval_price

                        if abs(edge) > 0.08:
                            sig = {
                                "market_id": overvalued["id"],
                                "question": overvalued.get("question", ""),
                                "signal_type": "COHERENCE",
                                "direction": "NO",
                                "confidence": round(min(0.65 + abs(edge), 0.85), 4),
                                "edge": round(edge, 4),
                                "predicted_prob": round(fair_price, 4),
                                "market_price": round(overval_price, 4),
                                "sentiment_score": 0.0,
                                "source": f"Incohérence logique avec '{group[0].get('question','')[:40]}'",
                                "texts_count": 0,
                                "market_url": overvalued.get("market_url", ""),
                                "urgency_bonus": overvalued.get("urgency_bonus", 0),
                                "category": overvalued.get("category", "other"),
                                "llm_reasoning": (
                                    f"Contradiction logique : '{m1.get('question','')[:40]}' à {p1:.0%} "
                                    f"+ '{m2.get('question','')[:40]}' à {p2:.0%} = {p1+p2:.0%} > 100%. "
                                    f"L'un est surévalué."
                                ),
                                "llm_valid": True,
                            }
                            await self.db.save_signal(sig)
                            signals.append(sig)
                            logger.info(
                                f"COHÉRENCE: {m1.get('question','')[:30]} ({p1:.0%}) + "
                                f"{m2.get('question','')[:30]} ({p2:.0%}) = {p1+p2:.0%}"
                            )

        return signals

    async def run_forever(self) -> None:
        """Boucle principale — combine les signaux et détecte les incohérences."""
        self._running = True
        logger.info("Signal Combiner démarré")
        while self._running:
            try:
                markets = await self.db.get_active_markets(limit=100)
                combined_count = 0
                for market in markets:
                    combined = await self.combine_signals(market["id"], market)
                    if combined:
                        combined_count += 1
                        # Sauvegarder le signal combiné
                        await self.db.save_signal({
                            "market_id": combined.market_id,
                            "question": combined.question,
                            "signal_type": "COMBINED",
                            "direction": combined.direction,
                            "confidence": combined.combined_confidence,
                            "edge": combined.combined_edge,
                            "predicted_prob": round(
                                market.get("yes_price", 0.5) + combined.combined_edge, 4
                            ),
                            "market_price": market.get("yes_price", 0.5),
                            "sentiment_score": 0.0,
                            "source": f"COMBINED({'+'.join(combined.source_types)})",
                            "texts_count": combined.source_count,
                            "market_url": market.get("market_url", ""),
                            "urgency_bonus": market.get("urgency_bonus", 0),
                            "category": market.get("category", "other"),
                            "llm_reasoning": f"Signal combiné de {combined.source_count} agents concordants.",
                            "llm_valid": True,
                        })
                if combined_count:
                    logger.info(f"Combiner: {combined_count} signaux combinés générés")

                # Détecter les incohérences inter-marchés
                coherence = await self.detect_coherence_signals()
                if coherence:
                    logger.info(f"Combiner: {len(coherence)} signaux de cohérence")

            except Exception as e:
                logger.error(f"SignalCombiner erreur: {e}")
            await asyncio.sleep(120)  # Toutes les 2 minutes

    def stop(self):
        self._running = False
        logger.info("Signal Combiner arrêté")
