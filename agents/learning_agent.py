"""
PolyPoly — Agent 5 : Apprentissage Continu
Analyse les trades perdants, identifie les patterns d'erreurs et améliore le système.
"""

import asyncio
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from config import (
    ANTHROPIC_API_KEY, LLM_MODEL, LLM_MAX_TOKENS,
    MIN_CONFIDENCE_THRESHOLD, MIN_EDGE_THRESHOLD,
    LEARNING_INTERVAL_SEC,
)
from utils.database import Database
try:
    from utils.telegram_bot import TelegramNotifier
except Exception:
    TelegramNotifier = object  # type: ignore


# Patterns d'erreurs connus
ERROR_PATTERNS = {
    "OVERCONFIDENCE": "Confiance trop élevée sur marchés à faible liquidité",
    "SENTIMENT_TRAP": "Sentiment positif sur marché déjà correctement pricé",
    "TIME_DECAY": "Trade ouvert trop proche de la résolution",
    "LOW_LIQUIDITY": "Trade sur marché sous-liquide — slippage élevé",
    "NARRATIVE_LAG": "Sentiment basé sur info déjà intégrée dans le prix",
    "EDGE_EROSION": "Edge réel bien inférieur à l'edge calculé",
    "CATEGORY_BIAS": "Performance systématiquement faible sur une catégorie",
    "CORRELATED_LOSS": "Plusieurs pertes sur marchés corrélés simultanément",
}


class LearningAgent:
    """
    Agent 5 — Apprentissage continu et amélioration.

    Responsabilités :
    - Analyse les trades perdants en profondeur
    - Identifie les patterns récurrents d'erreurs
    - Met à jour les seuils dynamiquement (DB)
    - Génère un rapport d'amélioration
    - Coordonne avec les autres agents via la DB
    """

    def __init__(self, db: Database, telegram: TelegramNotifier):
        self.db = db
        self.telegram = telegram
        self._running = False
        self._llm: Optional[object] = None
        self._improvements_made = 0

    async def run_forever(self) -> None:
        """Boucle principale."""
        if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
            self._llm = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            logger.info("LLM disponible pour Agent 5")

        # Initialiser les paramètres dynamiques par défaut
        await self._init_dynamic_params()

        self._running = True
        logger.info("Agent 5 (Apprentissage) démarré")

        while self._running:
            try:
                await self.learning_cycle()
            except Exception as e:
                logger.error(f"Apprentissage erreur: {e}")
                await self.telegram.notify_error(str(e), "Agent 5 - Learning")
            await asyncio.sleep(LEARNING_INTERVAL_SEC)

    async def _init_dynamic_params(self) -> None:
        """Initialise les paramètres dynamiques s'ils n'existent pas."""
        defaults = {
            "min_confidence_threshold": MIN_CONFIDENCE_THRESHOLD,
            "min_edge_threshold": MIN_EDGE_THRESHOLD,
            "max_position_size_usd": 5.0,
            "blacklisted_categories": [],
            "sentiment_weight": 0.4,
            "xgb_weight": 0.6,
            "learning_version": 1,
        }
        for key, value in defaults.items():
            existing = await self.db.get_param(key)
            if existing is None:
                await self.db.set_param(key, value, "Initialisation")

    async def learning_cycle(self) -> None:
        """Cycle complet d'apprentissage."""
        logger.info("Agent 5: cycle d'apprentissage...")

        stats = await self.db.get_trade_stats()
        total = stats.get("total", 0)

        if total < 5:
            logger.info("Agent 5: pas assez de trades pour apprendre (minimum 5)")
            return

        # 1. Analyser les trades perdants
        losing_trades = await self.db.get_losing_trades(limit=100)
        if losing_trades:
            patterns = await self._analyze_losing_patterns(losing_trades)
            await self._update_parameters(patterns, stats)

        # 2. Générer le rapport de performance
        await self._generate_performance_report(stats)

        # 3. Analyse LLM approfondie si disponible
        if self._llm and total >= 20:
            await self._llm_deep_analysis(stats, losing_trades[:20])

        # 4. Sauvegarder snapshot
        await self._save_snapshot(stats)

        logger.info(f"Agent 5: {self._improvements_made} améliorations appliquées")

    async def _analyze_losing_patterns(self, losing_trades: list[dict]) -> dict:
        """Analyse statistique des patterns dans les trades perdants."""
        patterns = defaultdict(int)

        for trade in losing_trades:
            confidence = trade.get("confidence", 0)
            edge = abs(trade.get("edge", 0))
            sentiment = abs(trade.get("sentiment_score", 0))
            size_usd = trade.get("size_usd", 0)

            # Détecter les patterns
            if confidence > 0.85:
                patterns["OVERCONFIDENCE"] += 1

            if sentiment > 0.5 and edge < 0.1:
                patterns["SENTIMENT_TRAP"] += 1

            # Vérifier liquidité via le marché
            market_data = json.loads(trade.get("raw_data", "{}") or "{}")
            liq = market_data.get("liquidity", 0)
            if liq and float(liq) < 2000:
                patterns["LOW_LIQUIDITY"] += 1

            if edge < MIN_EDGE_THRESHOLD * 1.2:
                patterns["EDGE_EROSION"] += 1

        # Enregistrer les patterns dans la DB
        for pattern_type, count in patterns.items():
            if count >= 2:
                avg_loss = sum(
                    abs(t.get("pnl", 0)) for t in losing_trades
                ) / len(losing_trades) if losing_trades else 0

                pattern_data = {
                    "pattern_type": pattern_type,
                    "description": ERROR_PATTERNS.get(pattern_type, pattern_type),
                    "avg_loss": avg_loss,
                    "conditions_json": json.dumps({"count": count}),
                    "mitigation": self._get_mitigation(pattern_type),
                }
                await self.db.save_learning_pattern(pattern_data)
                await self.db.increment_pattern(pattern_type)

        return dict(patterns)

    def _get_mitigation(self, pattern_type: str) -> str:
        """Retourne l'action corrective pour un pattern."""
        mitigations = {
            "OVERCONFIDENCE": "Augmenter seuil confiance min de 2%, réduire kelly",
            "SENTIMENT_TRAP": "Réduire poids sentiment, exiger edge XGBoost confirmé",
            "TIME_DECAY": "Augmenter min_time_to_resolution à 8h",
            "LOW_LIQUIDITY": "Augmenter min_liquidity_usd de 25%",
            "NARRATIVE_LAG": "Ajouter délai 30min après news majeure",
            "EDGE_EROSION": "Augmenter min_edge_threshold de 1%",
            "CATEGORY_BIAS": "Blacklister temporairement cette catégorie",
            "CORRELATED_LOSS": "Limiter positions corrélées à 2 simultanées",
        }
        return mitigations.get(pattern_type, "Analyser manuellement")

    async def _update_parameters(self, patterns: dict, stats: dict) -> None:
        """Met à jour les paramètres dynamiques basé sur les patterns détectés."""
        win_rate = stats.get("win_rate", 0)
        changes = []

        # --- Ajustement du seuil de confiance ---
        if "OVERCONFIDENCE" in patterns and patterns["OVERCONFIDENCE"] >= 3:
            current = await self.db.get_param("min_confidence_threshold", MIN_CONFIDENCE_THRESHOLD)
            new_val = min(current + 0.02, 0.90)
            await self.db.set_param(
                "min_confidence_threshold", new_val,
                "OVERCONFIDENCE détecté (≥3 occurrences)"
            )
            changes.append(f"Seuil confiance: {current:.2%} → {new_val:.2%}")
            self._improvements_made += 1

        # --- Ajustement de l'edge minimum ---
        if "EDGE_EROSION" in patterns and patterns["EDGE_EROSION"] >= 3:
            current = await self.db.get_param("min_edge_threshold", MIN_EDGE_THRESHOLD)
            new_val = min(current + 0.01, 0.15)
            await self.db.set_param(
                "min_edge_threshold", new_val,
                "EDGE_EROSION fréquent"
            )
            changes.append(f"Edge minimum: {current:.2%} → {new_val:.2%}")
            self._improvements_made += 1

        # --- Si le win rate est bon, relâcher légèrement ---
        if win_rate > 65 and stats.get("total", 0) >= 20:
            current_conf = await self.db.get_param("min_confidence_threshold", MIN_CONFIDENCE_THRESHOLD)
            if current_conf > MIN_CONFIDENCE_THRESHOLD + 0.04:
                new_val = max(current_conf - 0.01, MIN_CONFIDENCE_THRESHOLD)
                await self.db.set_param(
                    "min_confidence_threshold", new_val,
                    f"Win rate excellent ({win_rate:.1f}%) — détente légère"
                )
                changes.append(f"Seuil confiance abaissé: {current_conf:.2%} → {new_val:.2%}")

        # --- Poids sentiment ---
        if "SENTIMENT_TRAP" in patterns and patterns["SENTIMENT_TRAP"] >= 3:
            current = await self.db.get_param("sentiment_weight", 0.4)
            new_val = max(current - 0.05, 0.15)
            await self.db.set_param(
                "sentiment_weight", new_val,
                "SENTIMENT_TRAP récurrent"
            )
            changes.append(f"Poids sentiment: {current:.2f} → {new_val:.2f}")
            self._improvements_made += 1

        if changes:
            logger.info(f"Agent 5: Paramètres mis à jour — {', '.join(changes)}")
            for change in changes:
                pattern_key = list(patterns.keys())[0] if patterns else "OPTIMIZATION"
                await self.telegram.notify_learning_update(
                    pattern_key, change
                )

    async def _generate_performance_report(self, stats: dict) -> None:
        """Génère et log un rapport de performance."""
        win_rate = stats.get("win_rate", 0)
        total_pnl = stats.get("total_pnl", 0)
        total = stats.get("total", 0)

        if total == 0:
            return

        logger.info(
            f"Performance: {total} trades | "
            f"Win rate: {win_rate:.1f}% | "
            f"P&L: {total_pnl:+.2f}$ | "
            f"Avg edge: {stats.get('avg_edge', 0):.2%}"
        )

        # Rapport quotidien si premier cycle de la journée
        last_report = await self.db.get_param("last_daily_report")
        today = datetime.now().date().isoformat()
        if last_report != today:
            await self.telegram.notify_daily_report(stats)
            await self.db.set_param("last_daily_report", today, "Rapport quotidien")

    async def _llm_deep_analysis(self, stats: dict, recent_losers: list[dict]) -> None:
        """Analyse approfondie avec LLM des trades perdants."""
        if not self._llm or not recent_losers:
            return

        # Construire le résumé des trades perdants
        losers_summary = "\n".join([
            f"- [{t['direction']}] {t.get('question', 'N/A')[:60]} | "
            f"conf={t['confidence']:.2%} | edge={t['edge']:.2%} | "
            f"pnl={t.get('pnl', 0):.2f}$"
            for t in recent_losers[:15]
        ])

        existing_patterns = await self.db.get_learning_patterns()
        patterns_text = "\n".join(
            f"- {p['pattern_type']} (×{p['frequency']}): {p['description']}"
            for p in existing_patterns[:8]
        )

        prompt = f"""Tu es un expert en analyse de risque pour marchés de prédiction.

STATISTIQUES GLOBALES:
- Win rate: {stats.get('win_rate', 0):.1f}%
- P&L total: ${stats.get('total_pnl', 0):.2f}
- Total trades: {stats.get('total', 0)}
- Confiance moyenne: {stats.get('avg_confidence', 0):.2%}

TRADES PERDANTS RÉCENTS:
{losers_summary}

PATTERNS DÉJÀ CONNUS:
{patterns_text if patterns_text else "Aucun encore"}

Analyse ces données et identifie:
1. Les nouveaux patterns non encore répertoriés
2. Les ajustements les plus urgents à faire
3. Les catégories de marchés à éviter

Réponds en JSON:
{{
  "new_patterns": ["pattern1", "pattern2"],
  "urgent_actions": ["action1", "action2"],
  "categories_to_avoid": ["cat1"],
  "overall_assessment": "évaluation en 2 phrases"
}}"""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._llm.messages.create(
                    model=LLM_MODEL,
                    max_tokens=512,
                    messages=[{"role": "user", "content": prompt}],
                ),
            )

            text = response.content[0].text.strip()
            if "{" in text and "}" in text:
                start, end = text.index("{"), text.rindex("}") + 1
                analysis = json.loads(text[start:end])

                # Appliquer les actions urgentes
                for action in analysis.get("urgent_actions", [])[:3]:
                    logger.info(f"Agent 5 LLM recommande: {action}")

                # Blacklister les catégories problématiques
                cats_to_avoid = analysis.get("categories_to_avoid", [])
                if cats_to_avoid:
                    current_blacklist = await self.db.get_param("blacklisted_categories", [])
                    new_blacklist = list(set(current_blacklist + cats_to_avoid))
                    await self.db.set_param(
                        "blacklisted_categories", new_blacklist,
                        f"LLM analyse: éviter {cats_to_avoid}"
                    )

                assessment = analysis.get("overall_assessment", "")
                if assessment:
                    logger.info(f"Agent 5 LLM assessment: {assessment}")

                # Incrémenter la version d'apprentissage
                version = await self.db.get_param("learning_version", 1)
                await self.db.set_param(
                    "learning_version", version + 1,
                    f"LLM analysis iteration {version + 1}"
                )

        except Exception as e:
            logger.warning(f"LLM deep analysis erreur: {e}")

    async def _save_snapshot(self, stats: dict) -> None:
        """Sauvegarde un snapshot de performance."""
        snap = {
            "total_trades": stats.get("total", 0),
            "winning_trades": stats.get("wins", 0),
            "win_rate": stats.get("win_rate", 0),
            "total_pnl": stats.get("total_pnl", 0),
            "avg_edge": stats.get("avg_edge", 0),
            "avg_confidence": stats.get("avg_confidence", 0),
            "best_category": "N/A",
            "worst_pattern": "N/A",
        }

        patterns = await self.db.get_learning_patterns()
        if patterns:
            snap["worst_pattern"] = patterns[0]["pattern_type"]

        await self.db.save_performance_snapshot(snap)

    def stop(self):
        self._running = False
        logger.info("Agent 5 (Apprentissage) arrêté")
