"""
PolyPoly — Agent 3 : Prédiction XGBoost + LLM
Calcule la vraie probabilité d'un événement vs le prix du marché.
"""

import asyncio
import json
import os
import pickle
from datetime import datetime, timezone, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger

try:
    import xgboost as xgb
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import log_loss, roc_auc_score
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    logger.warning("XGBoost non disponible")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from config import (
    MIN_CONFIDENCE_THRESHOLD, MIN_EDGE_THRESHOLD,
    XGBOOST_MODEL_PATH, FEATURE_SCALER_PATH, XGBOOST_PARAMS,
    MIN_TRADES_FOR_TRAINING, ANTHROPIC_API_KEY, LLM_MODEL,
    LLM_MAX_TOKENS, LLM_TEMPERATURE, PREDICTION_INTERVAL_SEC,
)
from utils.database import Database
try:
    from utils.telegram_bot import TelegramNotifier
except Exception:
    TelegramNotifier = object  # type: ignore


class PredictionAgent:
    """
    Agent 3 — Prédiction hybride XGBoost + LLM.

    Responsabilités :
    - Construit les features pour chaque marché candidat
    - Prédit la probabilité réelle avec XGBoost
    - Enrichit l'analyse avec un LLM (Claude)
    - Ne génère un signal QUE si la confiance dépasse le seuil
    - Met à jour le modèle au fil des trades résolus
    """

    def __init__(self, db: Database, telegram: TelegramNotifier):
        self.db = db
        self.telegram = telegram
        self._running = False
        self._model: Optional[object] = None      # XGBoost
        self._scaler: Optional[object] = None     # StandardScaler
        self._llm: Optional[object] = None        # Anthropic client
        self._model_trained = False
        self._load_model()

    def _load_model(self) -> None:
        """Charge le modèle XGBoost et le scaler s'ils existent."""
        if not XGB_AVAILABLE:
            return
        if os.path.exists(XGBOOST_MODEL_PATH):
            try:
                with open(XGBOOST_MODEL_PATH, "rb") as f:
                    self._model = pickle.load(f)
                with open(FEATURE_SCALER_PATH, "rb") as f:
                    self._scaler = pickle.load(f)
                self._model_trained = True
                logger.info("Modèle XGBoost chargé")
            except Exception as e:
                logger.warning(f"Impossible de charger le modèle: {e}")

    def _save_model(self) -> None:
        if not self._model:
            return
        with open(XGBOOST_MODEL_PATH, "wb") as f:
            pickle.dump(self._model, f)
        with open(FEATURE_SCALER_PATH, "wb") as f:
            pickle.dump(self._scaler, f)
        logger.info("Modèle XGBoost sauvegardé")

    async def run_forever(self) -> None:
        """Boucle principale."""
        if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
            self._llm = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            logger.info("LLM (Claude) connecté")

        self._running = True
        logger.info("Agent 3 (Prédiction) démarré")

        while self._running:
            try:
                await self.prediction_cycle()
            except Exception as e:
                logger.error(f"Prédiction erreur: {e}")
                await self.telegram.notify_error(str(e), "Agent 3 - Prédiction")
            await asyncio.sleep(PREDICTION_INTERVAL_SEC)

    async def prediction_cycle(self) -> list[dict]:
        """Cycle de prédiction sur les meilleurs marchés."""
        markets = await self.db.get_active_markets(limit=50)
        if not markets:
            return []

        # Entraîner/re-entraîner le modèle si assez de données
        await self._maybe_retrain()

        signals = []
        for market in markets:
            try:
                signal = await self._predict_market(market)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.debug(f"Prédiction {market['id'][:8]}: {e}")

        logger.info(f"Prédiction: {len(signals)} signaux haute confiance générés")
        return signals

    def _build_features(self, market: dict, sentiment_score: float = 0.0) -> np.ndarray:
        """
        Construit le vecteur de features pour XGBoost.
        Features numériques uniquement.
        """
        yes_price = market.get("yes_price", 0.5)
        no_price = market.get("no_price", 0.5)
        liquidity = market.get("liquidity", 0)
        volume = market.get("volume_24h", 0)
        spread = market.get("spread", 0)
        anomaly = market.get("anomaly_score", 0)

        # Temps avant résolution (en heures)
        hours_to_expiry = 168  # 7 jours par défaut
        end_date_str = market.get("end_date")
        if end_date_str:
            try:
                if "Z" in str(end_date_str):
                    end_date_str = str(end_date_str).replace("Z", "+00:00")
                end_date = datetime.fromisoformat(str(end_date_str))
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
                delta = end_date - datetime.now(timezone.utc)
                hours_to_expiry = max(delta.total_seconds() / 3600, 0)
            except Exception:
                pass

        # Imbalance bid-ask
        price_imbalance = abs(yes_price - 0.5)
        implied_no = 1 - yes_price
        arbitrage_gap = abs(yes_price + no_price - 1.0)

        # Liquidity score normalisé
        liq_score = min(liquidity / 100_000, 1.0)
        vol_score = min(volume / 50_000, 1.0)

        # Features de timing
        time_score = 1 - min(hours_to_expiry / (30 * 24), 1.0)
        urgency = 1 / (1 + hours_to_expiry / 24)

        features = np.array([
            yes_price,              # Prix YES actuel
            no_price,               # Prix NO actuel
            price_imbalance,        # Distance par rapport à 50%
            spread,                 # Spread bid-ask
            arbitrage_gap,          # Écart de pricing
            liq_score,              # Liquidité normalisée
            vol_score,              # Volume normalisé
            anomaly,                # Score d'anomalie
            sentiment_score,        # Score de sentiment
            time_score,             # Progression temporelle
            urgency,                # Urgence temporelle
            hours_to_expiry / 24,   # Jours avant expiry
            yes_price * yes_price,  # Feature quadratique
            yes_price * sentiment_score,  # Interaction prix x sentiment
            min(volume / (liquidity + 1), 1.0),  # Ratio vol/liq
        ], dtype=np.float32)

        return features

    async def _predict_market(self, market: dict) -> Optional[dict]:
        """
        Génère une prédiction pour un marché.
        Retourne un signal seulement si la confiance est suffisante.
        """
        # Récupérer le sentiment pour ce marché
        sentiment = 0.0
        recent_signals = await self.db.get_recent_signals(limit=200)
        for sig in recent_signals:
            if sig["market_id"] == market["id"] and sig["signal_type"] == "SENTIMENT":
                sentiment = sig.get("sentiment_score", 0.0)
                break

        features = self._build_features(market, sentiment)
        yes_price = market.get("yes_price", 0.5)

        # --- Prédiction XGBoost ---
        xgb_prob = None
        if self._model_trained and self._model and XGB_AVAILABLE:
            try:
                features_scaled = self._scaler.transform(features.reshape(1, -1))
                proba = self._model.predict_proba(features_scaled)[0]
                xgb_prob = float(proba[1])
            except Exception as e:
                logger.debug(f"XGBoost predict erreur: {e}")

        # --- Prédiction LLM si XGBoost non disponible ou pour enrichir ---
        llm_prob = None
        llm_reasoning = ""
        if self._llm and (xgb_prob is None or abs((xgb_prob or 0.5) - yes_price) > 0.08):
            llm_result = await self._llm_predict(market, sentiment)
            if llm_result:
                llm_prob = llm_result.get("probability")
                llm_reasoning = llm_result.get("reasoning", "")

        # --- Combiner les prédictions ---
        if xgb_prob is not None and llm_prob is not None:
            predicted_prob = xgb_prob * 0.6 + llm_prob * 0.4
        elif xgb_prob is not None:
            predicted_prob = xgb_prob
        elif llm_prob is not None:
            predicted_prob = llm_prob
        else:
            return None  # Pas de prédiction possible

        # --- Calculer l'edge et la confiance ---
        edge = predicted_prob - yes_price
        abs_edge = abs(edge)

        if abs_edge < MIN_EDGE_THRESHOLD:
            return None

        # Confiance basée sur la magnitude de l'edge et la certitude du modèle
        base_confidence = min(0.5 + abs_edge * 2, 0.95)
        if xgb_prob is not None and llm_prob is not None:
            # Les deux modèles sont d'accord → plus confiant
            agreement = 1 - abs(xgb_prob - llm_prob)
            confidence = base_confidence * (0.7 + agreement * 0.3)
        else:
            confidence = base_confidence * 0.85  # Un seul modèle → moins confiant

        # Filtre final par seuil de confiance
        if confidence < MIN_CONFIDENCE_THRESHOLD:
            return None

        direction = "YES" if edge > 0 else "NO"

        signal = {
            "market_id": market["id"],
            "question": market.get("question", ""),
            "signal_type": "PREDICTION",
            "direction": direction,
            "confidence": round(confidence, 4),
            "edge": round(edge, 4),
            "predicted_prob": round(predicted_prob, 4),
            "market_price": round(yes_price, 4),
            "sentiment_score": round(sentiment, 4),
            "source": f"XGBoost({xgb_prob:.3f})" if xgb_prob else f"LLM({llm_prob:.3f})",
            "llm_reasoning": llm_reasoning,
            "features": features.tolist(),
        }

        await self.db.save_signal(signal)
        logger.info(
            f"Signal prédiction [{confidence:.2%}]: {direction} "
            f"{market['question'][:50]} | edge={edge:.2%}"
        )

        # Notifier Telegram si très haute confiance
        if confidence > 0.80:
            await self.telegram.notify_opportunity({**signal, "question": market.get("question")})

        return signal

    async def _llm_predict(self, market: dict, sentiment: float) -> Optional[dict]:
        """Appelle Claude pour enrichir l'analyse."""
        if not self._llm:
            return None

        yes_price = market.get("yes_price", 0.5)
        question = market.get("question", "")
        liquidity = market.get("liquidity", 0)
        volume = market.get("volume_24h", 0)

        # Récupérer les patterns d'erreurs connus
        patterns = await self.db.get_learning_patterns()
        patterns_text = "\n".join(
            f"- {p['pattern_type']}: {p['description']}" for p in patterns[:5]
        )

        prompt = f"""Tu es un analyste expert en marchés de prédiction Polymarket.

Marché: "{question}"
Prix actuel YES: {yes_price:.1%} ({yes_price*100:.1f}¢)
Liquidité: ${liquidity:,.0f}
Volume 24h: ${volume:,.0f}
Score sentiment: {sentiment:.3f} (-1=négatif, +1=positif)

Erreurs passées à éviter:
{patterns_text if patterns_text else "Aucun pattern connu encore"}

Analyse ce marché et estime la probabilité RÉELLE que l'événement se produise.
Sois précis, factuel, et base-toi sur l'état du monde actuel.

Réponds UNIQUEMENT en JSON:
{{
  "probability": 0.XX,
  "confidence": "high|medium|low",
  "reasoning": "explication concise en 2 phrases max",
  "key_factor": "le facteur le plus déterminant"
}}"""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._llm.messages.create(
                    model=LLM_MODEL,
                    max_tokens=256,
                    temperature=LLM_TEMPERATURE,
                    messages=[{"role": "user", "content": prompt}],
                ),
            )

            text = response.content[0].text.strip()
            # Extraire le JSON
            if "{" in text and "}" in text:
                start = text.index("{")
                end = text.rindex("}") + 1
                data = json.loads(text[start:end])
                return {
                    "probability": float(data.get("probability", 0.5)),
                    "reasoning": data.get("reasoning", ""),
                }
        except Exception as e:
            logger.debug(f"LLM predict erreur: {e}")

        return None

    async def _maybe_retrain(self) -> None:
        """Ré-entraîne le modèle si assez de trades résolus."""
        if not XGB_AVAILABLE:
            return

        closed_trades = await self.db.get_closed_trades(limit=500)
        if len(closed_trades) < MIN_TRADES_FOR_TRAINING:
            return

        # Vérifier si un entraînement récent a eu lieu
        last_train = await self.db.get_param("last_model_training")
        if last_train:
            last_dt = datetime.fromisoformat(last_train)
            if datetime.now() - last_dt < timedelta(hours=6):
                return

        logger.info(f"Re-entraînement XGBoost sur {len(closed_trades)} trades...")
        await self._train_model(closed_trades)

    async def _train_model(self, trades: list[dict]) -> None:
        """Entraîne le modèle XGBoost sur l'historique des trades."""
        if not XGB_AVAILABLE or len(trades) < MIN_TRADES_FOR_TRAINING:
            return

        X_list = []
        y_list = []

        for trade in trades:
            features_json = trade.get("features_json")
            if not features_json:
                continue
            try:
                features = json.loads(features_json)
                if not features:
                    continue
                X_list.append(features)
                y_list.append(1 if trade["status"] == "WON" else 0)
            except Exception:
                continue

        if len(X_list) < MIN_TRADES_FOR_TRAINING:
            return

        X = np.array(X_list, dtype=np.float32)
        y = np.array(y_list)

        # Scaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Split
        if len(X) > 40:
            X_train, X_val, y_train, y_val = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
        else:
            X_train, X_val, y_train, y_val = X_scaled, X_scaled, y, y

        # Entraîner XGBoost
        model = xgb.XGBClassifier(**XGBOOST_PARAMS)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        # Évaluation
        y_pred = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, y_pred) if len(set(y_val)) > 1 else 0.5
        ll = log_loss(y_val, y_pred)

        logger.info(f"Modèle XGBoost: AUC={auc:.3f}, LogLoss={ll:.3f}")

        self._model = model
        self._scaler = scaler
        self._model_trained = True
        self._save_model()

        await self.db.set_param(
            "last_model_training",
            datetime.now().isoformat(),
            f"AUC={auc:.3f}, n_trades={len(trades)}"
        )

    def stop(self):
        self._running = False
        logger.info("Agent 3 (Prédiction) arrêté")
