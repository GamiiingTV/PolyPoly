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

    def __init__(self, db: Database, telegram: TelegramNotifier, ob_agent=None):
        self.db = db
        self.telegram = telegram
        self._running = False
        self._model: Optional[object] = None
        self._scaler: Optional[object] = None
        self._llm: Optional[object] = None
        self._ob_agent = ob_agent   # Agent 6 (order book), optionnel
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

        # Pré-entraîner XGBoost sur l'historique Polymarket si pas encore fait
        if XGB_AVAILABLE and not self._model_trained:
            logger.info("XGBoost non entraîné — téléchargement historique Polymarket...")
            await self._pretrain_on_polymarket_history()

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

    def _build_features(self, market: dict, sentiment_score: float = 0.0,
                        ob_features: dict = None, price_history: list = None) -> np.ndarray:
        """
        Construit le vecteur de 35 features pour XGBoost.
        AMÉLIORÉ : +20 features (volatilité, microstructure, momentum, temporel, catégorie)
        """
        yes_price = market.get("yes_price", 0.5)
        no_price = market.get("no_price", 0.5)
        liquidity = market.get("liquidity", 0)
        volume = market.get("volume_24h", 0)
        spread = market.get("spread", 0)
        anomaly = market.get("anomaly_score", 0)
        ob = ob_features or {}

        # --- Temps avant résolution ---
        hours_to_expiry = 168.0
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

        # --- Features de base ---
        price_imbalance = abs(yes_price - 0.5)
        arbitrage_gap = abs(yes_price + no_price - 1.0)
        liq_score = min(liquidity / 100_000, 1.0)
        vol_score = min(volume / 50_000, 1.0)
        time_score = 1 - min(hours_to_expiry / (30 * 24), 1.0)
        urgency = 1 / (1 + hours_to_expiry / 24)
        vol_liq_ratio = min(volume / (liquidity + 1), 1.0)

        # --- Features de volatilité (depuis l'historique des prix) ---
        price_volatility = 0.0
        price_momentum_5m = 0.0
        price_momentum_15m = 0.0
        price_velocity = 0.0
        mean_reversion_signal = 0.0
        prices_recent = []

        if price_history and len(price_history) >= 3:
            prices_recent = [h.get("yes_price", yes_price) for h in price_history[-10:]]
            if len(prices_recent) >= 2:
                price_volatility = float(np.std(prices_recent))
                # Momentum : prix actuel vs il y a N mesures
                if len(prices_recent) >= 5:
                    price_momentum_5m = yes_price - prices_recent[-5]
                if len(prices_recent) >= 10:
                    price_momentum_15m = yes_price - prices_recent[-10]
                # Vélocité : dérivée du prix (changement par unité de temps)
                if len(prices_recent) >= 2:
                    price_velocity = prices_recent[-1] - prices_recent[-2]
                # Régression vers la moyenne : écart par rapport à la moyenne récente
                mean_price = float(np.mean(prices_recent))
                mean_reversion_signal = yes_price - mean_price

        # --- Features de microstructure order book ---
        obi = float(ob.get("obi", 0.0))
        bid_depth_norm = min(float(ob.get("bid_depth", 0)) / 10000, 1.0)
        ask_depth_norm = min(float(ob.get("ask_depth", 0)) / 10000, 1.0)
        depth_ratio = float(ob.get("depth_ratio", 1.0))
        whale_bid_ratio = float(ob.get("whale_bid_ratio", 0.0))
        whale_ask_ratio = float(ob.get("whale_ask_ratio", 0.0))
        ob_spread = float(ob.get("ob_spread", spread))
        is_thin_book = float(ob.get("is_thin", 0))
        obi_trend = float(ob.get("obi_trend", 0.0))

        # --- Features temporelles (heure, jour) ---
        now = datetime.now()
        hour_of_day = now.hour / 24.0      # Heure normalisée (0-1)
        day_of_week = now.weekday() / 6.0  # Jour normalisé (0=lun, 1=dim)
        is_weekend = float(now.weekday() >= 5)
        # Heures de trading US (14h-22h UTC = prime time Polymarket)
        is_us_prime_time = float(14 <= now.hour <= 22)

        # --- Features d'interaction ---
        price_x_sentiment = yes_price * sentiment_score
        price_x_obi = yes_price * obi
        sentiment_x_momentum = sentiment_score * price_momentum_5m
        volume_x_anomaly = vol_score * anomaly
        urgency_x_obi = urgency * abs(obi)

        # --- Vecteur final (35 features) ---
        features = np.array([
            # Groupe 1 : Prix (5)
            yes_price,
            no_price,
            price_imbalance,
            arbitrage_gap,
            spread,
            # Groupe 2 : Volume & Liquidité (4)
            liq_score,
            vol_score,
            vol_liq_ratio,
            anomaly,
            # Groupe 3 : Timing (5)
            time_score,
            urgency,
            hours_to_expiry / 24.0,
            hour_of_day,
            day_of_week,
            # Groupe 4 : Volatilité & Momentum (5)
            price_volatility,
            price_momentum_5m,
            price_momentum_15m,
            price_velocity,
            mean_reversion_signal,
            # Groupe 5 : Order Book (5)
            obi,
            bid_depth_norm,
            ask_depth_norm,
            depth_ratio,
            obi_trend,
            # Groupe 6 : Activité Baleine (3)
            whale_bid_ratio,
            whale_ask_ratio,
            is_thin_book,
            # Groupe 7 : Sentiment (2)
            sentiment_score,
            abs(sentiment_score),
            # Groupe 8 : Contexte marché (3)
            is_weekend,
            is_us_prime_time,
            ob_spread,
            # Groupe 9 : Interactions (3)
            price_x_sentiment,
            price_x_obi,
            urgency_x_obi,
        ], dtype=np.float32)

        return features

    FEATURE_COUNT = 35  # Nombre total de features

    async def _predict_market(self, market: dict) -> Optional[dict]:
        """
        Génère une prédiction pour un marché.
        AMÉLIORÉ : utilise les 35 features (ordre book + momentum + temporel).
        """
        market_id = market["id"]

        # Sentiment
        sentiment = 0.0
        recent_signals = await self.db.get_recent_signals(limit=200)
        for sig in recent_signals:
            if sig["market_id"] == market_id and sig["signal_type"] == "SENTIMENT":
                sentiment = sig.get("sentiment_score", 0.0)
                break

        # Order Book features (si l'agent OrderBook tourne)
        ob_features = {}
        if self._ob_agent:
            try:
                ob_features = await self._ob_agent.get_orderbook_features(market_id)
            except Exception:
                pass

        # Historique des prix pour volatilité/momentum
        price_history = await self.db.get_price_history(market_id, minutes=30)

        features = self._build_features(market, sentiment, ob_features, price_history)
        yes_price = market.get("yes_price", 0.5)
        category = market.get("category", "other")

        # Filtre : marché quasi-résolu → aucun edge possible, on ne prédit pas
        if yes_price < 0.15 or yes_price > 0.85:
            return None

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

        # --- Sports : XGBoost seul est aveugle (pas de features sportives) ---
        # XGBoost ne connaît pas les équipes, les pitchers, la météo, les stats.
        # Sur marchés sports, seul le LLM peut apporter un vrai raisonnement.
        # Sans LLM disponible → on ne génère pas de signal sports.
        if category == "sports" and llm_prob is None:
            return None

        # --- Combiner les prédictions ---
        if xgb_prob is not None and llm_prob is not None:
            # LLM = source principale, XGBoost = ajustement mineur
            predicted_prob = llm_prob * 0.70 + xgb_prob * 0.30
        elif llm_prob is not None:
            predicted_prob = llm_prob
        elif xgb_prob is not None:
            # XGBoost seul : uniquement pour marchés non-sports, avec prudence
            predicted_prob = xgb_prob
        else:
            return None  # Pas de prédiction possible

        # Plafonner la probabilité prédite (XGBoost peut diverger sans calibration)
        predicted_prob = min(max(predicted_prob, 0.10), 0.90)

        # --- Calculer l'edge et la confiance ---
        edge = predicted_prob - yes_price
        abs_edge = abs(edge)

        # Seuils d'edge minimaux par catégorie
        # Sports = très efficient → edge minimum 12%
        # Autres  = 5% (MIN_EDGE_THRESHOLD)
        min_edge = 0.12 if category == "sports" else MIN_EDGE_THRESHOLD
        if abs_edge < min_edge:
            return None

        # Confiance : basée sur edge + nombre de modèles d'accord
        # Plafond agressif pour XGBoost seul : max 0.68 (jamais de notification sans LLM)
        if xgb_prob is not None and llm_prob is not None:
            agreement = 1 - abs(xgb_prob - llm_prob)
            base_confidence = min(0.5 + abs_edge * 1.5, 0.88)
            confidence = base_confidence * (0.75 + agreement * 0.25)
        elif llm_prob is not None:
            # LLM seul = fiable
            base_confidence = min(0.5 + abs_edge * 1.5, 0.85)
            confidence = base_confidence * 0.90
        else:
            # XGBoost seul = peu fiable, plafond à 0.65
            base_confidence = min(0.5 + abs_edge * 1.0, 0.65)
            confidence = base_confidence * 0.80

        # Plafonds finaux par cas
        if xgb_prob is not None and llm_prob is not None:
            confidence = min(confidence, 0.82)   # LLM + XGBoost
        elif llm_prob is not None:
            confidence = min(confidence, 0.78)   # LLM seul
        else:
            confidence = min(confidence, 0.62)   # XGBoost seul (jamais ≥ seuil notif)

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

        # Notifier Telegram uniquement si LLM impliqué ET confiance suffisante
        # XGBoost seul (plafonné à 0.62) ne déclenchera jamais cette condition
        if confidence > 0.74 and llm_prob is not None:
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

    async def _pretrain_on_polymarket_history(self) -> None:
        """
        Télécharge des marchés résolus depuis la Gamma API et pré-entraîne
        XGBoost immédiatement — sans attendre 50 trades paper.
        Utilise les 500 derniers marchés résolus comme données d'entraînement.
        """
        if not XGB_AVAILABLE:
            return
        try:
            import httpx as _httpx
            logger.info("Téléchargement historique Polymarket pour pré-entraînement...")
            async with _httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    "https://gamma-api.polymarket.com/markets",
                    params={
                        "closed": "true",
                        "limit": 500,
                        "order": "volume",
                        "ascending": "false",
                    },
                )
            if resp.status_code != 200:
                logger.warning(f"Gamma API historique: HTTP {resp.status_code}")
                return

            raw_markets = resp.json()
            if not isinstance(raw_markets, list):
                raw_markets = raw_markets.get("markets", [])

            logger.info(f"Historique: {len(raw_markets)} marchés résolus récupérés")

            X_list, y_list = [], []
            for raw in raw_markets:
                # Label : YES si le marché s'est résolu YES (prix final proche de 1)
                res = raw.get("resolution") or raw.get("resolutionSource", "")
                outcome_prices_raw = raw.get("outcomePrices", [])
                if isinstance(outcome_prices_raw, str):
                    try:
                        import ast as _ast
                        outcome_prices_raw = _ast.literal_eval(outcome_prices_raw)
                    except Exception:
                        outcome_prices_raw = []
                final_price = float(outcome_prices_raw[0]) if outcome_prices_raw else 0.5
                if res == "YES" or final_price >= 0.95:
                    label = 1
                elif res == "NO" or final_price <= 0.05:
                    label = 0
                else:
                    continue  # Ignorer les marchés ambigus

                # Construire un vecteur de features simplifié depuis les données disponibles
                try:
                    yes_p = float(raw.get("bestAsk") or raw.get("lastTradePrice") or 0.5)
                    no_p = 1.0 - yes_p
                    liq = float(raw.get("liquidity") or 0)
                    vol = float(raw.get("volume") or 0)
                    spread = abs(
                        float(raw.get("bestAsk") or 0.5) - float(raw.get("bestBid") or 0.5)
                    )

                    # Features de base (sous-ensemble des 35 features)
                    features = np.array([
                        yes_p, no_p, liq / 100_000, vol / 50_000,
                        spread, abs(yes_p - 0.5),
                        min(liq / 100_000, 1.0),
                        min(vol / 50_000, 1.0),
                        yes_p * no_p,  # Incertitude
                        abs(yes_p + no_p - 1.0),  # Arbitrage gap
                        1.0 if yes_p > 0.5 else 0.0,
                        float(bool(raw.get("volume24hr", 0))),
                        min(float(raw.get("volume24hr") or 0) / 10_000, 1.0),
                        0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0,  # Features temporelles (inconnues)
                        0.0, 0.0, 0.0, 0.0, 0.0,
                        0.0, 0.0, 0.0, 0.0, 0.0,
                        0.0, 0.0, 0.0, 0.0, 0.0,
                    ], dtype=np.float32)

                    # S'assurer d'avoir exactement 35 features
                    if len(features) < 35:
                        features = np.pad(features, (0, 35 - len(features)))
                    features = features[:35]

                    X_list.append(features)
                    y_list.append(label)
                except Exception:
                    continue

            if len(X_list) < 50:
                logger.warning(f"Pré-entraînement: seulement {len(X_list)} exemples valides")
                return

            logger.info(f"Pré-entraînement XGBoost sur {len(X_list)} marchés historiques...")
            X = np.array(X_list, dtype=np.float32)
            y = np.array(y_list)

            from sklearn.preprocessing import StandardScaler
            from sklearn.model_selection import train_test_split
            import xgboost as xgb

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            X_train, X_val, y_train, y_val = train_test_split(
                X_scaled, y, test_size=0.15, random_state=42
            )

            from config import XGBOOST_PARAMS
            model = xgb.XGBClassifier(**{**XGBOOST_PARAMS, "n_estimators": 200})
            model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

            self._model = model
            self._scaler = scaler
            self._model_trained = True
            self._save_model()

            from sklearn.metrics import roc_auc_score
            y_pred = model.predict_proba(X_val)[:, 1]
            auc = roc_auc_score(y_val, y_pred)
            logger.info(
                f"XGBoost pré-entraîné sur {len(X_list)} marchés historiques | "
                f"AUC = {auc:.3f}"
            )
            await self.db.set_param(
                "last_model_training",
                datetime.now().isoformat(),
                f"Pré-entraînement historique Polymarket ({len(X_list)} marchés)"
            )

        except Exception as e:
            logger.warning(f"Pré-entraînement historique échoué: {e}")

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
