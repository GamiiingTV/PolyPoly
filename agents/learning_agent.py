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

    def __init__(self, db: Database, telegram: TelegramNotifier,
                 llm_validator=None):
        self.db = db
        self.telegram = telegram
        self._running = False
        self._llm: Optional[object] = None
        self._llm_validator = llm_validator   # référence au LLMValidator pour calibration
        self._improvements_made = 0
        self._calibration_fed: set[int] = set()  # trade IDs déjà envoyés au calibrateur

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
        """Cycle complet d'apprentissage — AMÉLIORÉ."""
        logger.info("Agent 5: cycle d'apprentissage...")

        stats = await self.db.get_trade_stats()
        total = stats.get("total", 0)

        if total < 5:
            logger.info("Agent 5: pas assez de trades pour apprendre (minimum 5)")
            return

        losing_trades = await self.db.get_losing_trades(limit=100)
        closed_trades = await self.db.get_closed_trades(limit=500)

        # 1. Analyser les patterns d'erreurs
        if losing_trades:
            patterns = await self._analyze_losing_patterns(losing_trades)
            await self._update_parameters(patterns, stats)

        # 2. Analyse par catégorie de marché
        if total >= 15:
            await self._analyze_by_category(closed_trades)

        # 3. Importance des features XGBoost
        if total >= 50:
            await self._analyze_feature_importance(closed_trades)

        # 4. Rapport de performance
        await self._generate_performance_report(stats)

        # 5. Calibration LLM — feedback boucle fermée
        await self._update_llm_calibration(closed_trades)

        # 6. Analyse LLM approfondie
        if self._llm and total >= 20:
            await self._llm_deep_analysis(stats, losing_trades[:20])

        # 7. Snapshot
        await self._save_snapshot(stats)

        logger.info(f"Agent 5: {self._improvements_made} améliorations appliquées")

    async def _update_llm_calibration(self, closed_trades: list[dict]) -> None:
        """
        Boucle de calibration fermée : pour chaque trade résolu,
        envoie (prob_LLM, outcome) au LLMValidator pour qu'il suive
        sa propre précision et ajuste son niveau de confiance en conséquence.
        """
        if not self._llm_validator:
            return

        new_fed = 0
        for trade in closed_trades:
            trade_id = trade.get("id")
            if not trade_id or trade_id in self._calibration_fed:
                continue

            llm_prob = trade.get("llm_prob") or trade.get("confidence")
            if llm_prob is None:
                continue

            status = trade.get("status", "")
            if status not in ("WON", "LOST"):
                continue

            outcome = (status == "WON")
            self._llm_validator.record_outcome(float(llm_prob), outcome)
            self._calibration_fed.add(trade_id)
            new_fed += 1

        if new_fed:
            cal = getattr(self._llm_validator, "_calibration_score", None)
            if cal is not None:
                await self.db.set_param(
                    "llm_calibration_score", round(cal, 4),
                    f"Mis à jour après {new_fed} résolutions"
                )
                logger.info(f"LLM Calibration: score={cal:.2f} ({new_fed} nouveaux trades intégrés)")

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

    async def _analyze_by_category(self, closed_trades: list[dict]) -> None:
        """
        Analyse les performances par catégorie de marché.
        Blackliste automatiquement les catégories avec win rate < 35%.
        """
        from collections import defaultdict
        cat_stats: dict = defaultdict(lambda: {"wins": 0, "total": 0, "pnl": 0.0})

        for trade in closed_trades:
            # Récupérer la catégorie depuis le marché en DB
            market = await self.db.get_market(trade.get("market_id", ""))
            category = market.get("category", "unknown") if market else "unknown"
            if not category:
                category = "unknown"

            cat_stats[category]["total"] += 1
            if trade.get("status") == "WON":
                cat_stats[category]["wins"] += 1
            cat_stats[category]["pnl"] += trade.get("pnl", 0) or 0

        best_cat = ""
        best_wr = 0.0
        auto_blacklisted = []

        for cat, s in cat_stats.items():
            if s["total"] < 5:
                continue
            wr = s["wins"] / s["total"]
            if wr > best_wr:
                best_wr, best_cat = wr, cat

            # Blacklister si très mauvaises performances
            if wr < 0.35 and s["total"] >= 8:
                current_bl = await self.db.get_param("blacklisted_categories", [])
                if cat not in current_bl:
                    new_bl = current_bl + [cat]
                    await self.db.set_param(
                        "blacklisted_categories", new_bl,
                        f"Win rate {wr:.0%} < 35% sur {s['total']} trades"
                    )
                    auto_blacklisted.append(cat)
                    self._improvements_made += 1
                    logger.warning(f"Catégorie blacklistée auto: '{cat}' (win rate {wr:.0%})")
                    await self.telegram.notify_learning_update(
                        "CATEGORY_BIAS",
                        f"Catégorie '{cat}' blacklistée: win rate {wr:.0%} < 35%"
                    )

        if best_cat:
            await self.db.set_param("best_category", best_cat, f"Win rate {best_wr:.0%}")
            logger.info(f"Meilleure catégorie: '{best_cat}' ({best_wr:.0%} win rate)")

        # Sauvegarder les win rates par catégorie pour calibration des signaux
        category_win_rates = {
            cat: round(s["wins"] / s["total"], 3)
            for cat, s in cat_stats.items()
            if s["total"] >= 5
        }
        if category_win_rates:
            await self.db.set_param(
                "category_win_rates", category_win_rates,
                "Calibration automatique par catégorie"
            )
            logger.info(f"Win rates par catégorie mis à jour: {category_win_rates}")

    async def _analyze_feature_importance(self, closed_trades: list[dict]) -> None:
        """
        Analyse l'importance des features XGBoost pour identifier les features
        les plus prédictives et celles qui introduisent du bruit.
        """
        try:
            import os, pickle
            from config import XGBOOST_MODEL_PATH
            if not os.path.exists(XGBOOST_MODEL_PATH):
                return

            with open(XGBOOST_MODEL_PATH, "rb") as f:
                model = pickle.load(f)

            importances = model.feature_importances_
            feature_names = [
                # Groupe 1: Prix
                "yes_price", "no_price", "price_imbalance", "arb_gap", "spread",
                # Groupe 2: Volume
                "liq_score", "vol_score", "vol_liq_ratio", "anomaly",
                # Groupe 3: Timing
                "time_score", "urgency", "days_to_expiry", "hour_of_day", "day_of_week",
                # Groupe 4: Volatilité
                "volatility", "momentum_5m", "momentum_15m", "velocity", "mean_rev",
                # Groupe 5: Order Book
                "obi", "bid_depth", "ask_depth", "depth_ratio", "obi_trend",
                # Groupe 6: Baleines
                "whale_bid", "whale_ask", "is_thin",
                # Groupe 7: Sentiment
                "sentiment", "abs_sentiment",
                # Groupe 8: Contexte
                "is_weekend", "is_us_prime", "ob_spread",
                # Groupe 9: Interactions
                "price_x_sent", "price_x_obi", "urgency_x_obi",
            ]

            # Trier par importance
            sorted_pairs = sorted(
                zip(feature_names[:len(importances)], importances),
                key=lambda x: -x[1]
            )

            top5 = sorted_pairs[:5]
            bottom5 = sorted_pairs[-5:]

            top_str = ", ".join(f"{n}={v:.3f}" for n, v in top5)
            bottom_str = ", ".join(f"{n}={v:.3f}" for n, v in bottom5)

            logger.info(f"Features importantes: {top_str}")
            logger.info(f"Features faibles: {bottom_str}")

            # Sauvegarder pour les rapports
            await self.db.set_param(
                "top_features", {n: float(v) for n, v in top5},
                "XGBoost feature importance"
            )
            await self.db.set_param(
                "weak_features", {n: float(v) for n, v in bottom5},
                "XGBoost feature importance"
            )

        except Exception as e:
            logger.debug(f"Feature importance erreur: {e}")

    async def _save_snapshot(self, stats: dict) -> None:
        """Sauvegarde un snapshot de performance."""
        best_cat = await self.db.get_param("best_category", "N/A")
        snap = {
            "total_trades": stats.get("total", 0),
            "winning_trades": stats.get("wins", 0),
            "win_rate": stats.get("win_rate", 0),
            "total_pnl": stats.get("total_pnl", 0),
            "avg_edge": stats.get("avg_edge", 0),
            "avg_confidence": stats.get("avg_confidence", 0),
            "best_category": best_cat or "N/A",
            "worst_pattern": "N/A",
        }

        patterns = await self.db.get_learning_patterns()
        if patterns:
            snap["worst_pattern"] = patterns[0]["pattern_type"]

        await self.db.save_performance_snapshot(snap)

    def stop(self):
        self._running = False
        logger.info("Agent 5 (Apprentissage) arrêté")
