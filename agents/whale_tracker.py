"""
PolyPoly — Agent 10 : Détecteur de Whales & Vélocité d'Ordres
Détecte les mouvements de "smart money" via l'analyse du flux de trades.

Stratégies :
1. Vélocité anormale : volume qui triple en 10 min sur un marché = signal
2. Concentration d'ordres : beaucoup de gros ordres dans la même direction
3. Divergence prix/volume : prix stable mais volume explose = accumulation
"""

import asyncio
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Optional
from loguru import logger

from utils.database import Database
from utils.polymarket_api import GammaAPI, CLOBClient

# Seuils de détection
VOLUME_SPIKE_MULTIPLIER = 2.5   # Volume 2.5x la normale = spike
LARGE_ORDER_USD = 200.0          # Ordre >$200 = "gros" ordre
MIN_ORDERS_FOR_SIGNAL = 3        # Min 3 gros ordres dans la même direction
VELOCITY_WINDOW_MIN = 15         # Fenêtre d'analyse : 15 minutes
WHALE_SIGNAL_COOLDOWN_MIN = 60   # Un signal par marché max toutes les 60 min


class MarketVelocity:
    """Suivi de la vélocité d'un marché spécifique."""

    def __init__(self, market_id: str):
        self.market_id = market_id
        self.trade_timestamps: deque = deque(maxlen=200)
        self.volume_history: deque = deque(maxlen=50)  # volumes par fenêtre
        self.last_signal_at: Optional[datetime] = None

    def add_trade(self, volume_usd: float, timestamp: datetime):
        self.trade_timestamps.append((timestamp, volume_usd))

    def compute_velocity(self) -> tuple[float, float]:
        """
        Retourne (volume_recent, volume_baseline) sur les 15 dernières minutes
        comparé aux 15 minutes précédentes.
        """
        now = datetime.now(timezone.utc)
        window = timedelta(minutes=VELOCITY_WINDOW_MIN)

        recent_vol = sum(
            v for t, v in self.trade_timestamps
            if now - t <= window
        )
        baseline_vol = sum(
            v for t, v in self.trade_timestamps
            if window < now - t <= window * 2
        )

        return recent_vol, max(baseline_vol, 1.0)

    def is_cooling_down(self) -> bool:
        if not self.last_signal_at:
            return False
        age = (datetime.now(timezone.utc) - self.last_signal_at).total_seconds()
        return age < WHALE_SIGNAL_COOLDOWN_MIN * 60


class WhaleTracker:
    """
    Agent 10 — Détection de smart money via vélocité d'ordres.

    Surveille le flux de trades sur tous les marchés actifs.
    Quand un marché voit son volume tripler sans news visible,
    c'est souvent qu'un insider ou whale a bougé.
    """

    def __init__(self, db: Database, gamma: GammaAPI, clob: CLOBClient):
        self.db = db
        self.gamma = gamma
        self.clob = clob
        self._running = False
        self._velocities: dict[str, MarketVelocity] = {}
        self._signals_generated = 0

    async def run_forever(self) -> None:
        self._running = True
        logger.info("Agent 10 (WhaleTracker) démarré")
        while self._running:
            try:
                await self._scan_cycle()
            except Exception as e:
                logger.error(f"WhaleTracker erreur: {e}")
            await asyncio.sleep(120)  # Scan toutes les 2 minutes

    async def _scan_cycle(self) -> list[dict]:
        """Cycle de détection de vélocité anormale."""
        markets = await self.db.get_active_markets(limit=100)
        whale_signals = []

        for market in markets:
            market_id = market.get("id", "")
            if not market_id:
                continue

            if market_id not in self._velocities:
                self._velocities[market_id] = MarketVelocity(market_id)

            mv = self._velocities[market_id]
            if mv.is_cooling_down():
                continue

            # Récupérer les trades récents via Gamma API
            try:
                recent_trades = await self.gamma.get_trades(
                    market_id=market_id, limit=50
                )
            except Exception:
                continue

            if not recent_trades:
                continue

            # Enregistrer les trades
            now = datetime.now(timezone.utc)
            for trade in recent_trades:
                try:
                    ts_str = trade.get("timestamp") or trade.get("created_at", "")
                    if ts_str:
                        ts = datetime.fromisoformat(
                            str(ts_str).replace("Z", "+00:00")
                        )
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                    else:
                        ts = now
                    vol = float(trade.get("amount", 0) or trade.get("size", 0) or 0)
                    mv.add_trade(vol, ts)
                except Exception:
                    continue

            # Analyser la vélocité
            recent_vol, baseline_vol = mv.compute_velocity()
            ratio = recent_vol / baseline_vol

            if ratio >= VOLUME_SPIKE_MULTIPLIER and recent_vol > 50:
                signal = await self._generate_whale_signal(
                    market, recent_vol, baseline_vol, ratio, recent_trades
                )
                if signal:
                    mv.last_signal_at = now
                    whale_signals.append(signal)
                    self._signals_generated += 1

        if whale_signals:
            logger.info(
                f"WhaleTracker: {len(whale_signals)} spike(s) détecté(s)"
            )
        return whale_signals

    async def _generate_whale_signal(
        self,
        market: dict,
        recent_vol: float,
        baseline_vol: float,
        ratio: float,
        trades: list[dict],
    ) -> Optional[dict]:
        """Génère un signal WHALE si la vélocité est vraiment anormale."""
        # Déterminer la direction dominante des gros trades
        yes_vol = 0.0
        no_vol = 0.0

        for t in trades:
            side = str(t.get("side", t.get("outcome", ""))).upper()
            vol = float(t.get("amount", 0) or t.get("size", 0) or 0)
            if "YES" in side or side == "BUY":
                yes_vol += vol
            elif "NO" in side or side == "SELL":
                no_vol += vol

        if yes_vol + no_vol < 10:
            return None

        direction = "YES" if yes_vol > no_vol else "NO"
        dominant_vol = max(yes_vol, no_vol)
        total_vol = yes_vol + no_vol
        directional_pct = dominant_vol / total_vol

        # Signal seulement si la direction est claire (>60% dans un sens)
        if directional_pct < 0.60:
            return None

        yes_price = market.get("yes_price", 0.5)
        edge = (0.65 - yes_price) if direction == "YES" else (yes_price - 0.65)
        confidence = min(0.65 + (ratio - VOLUME_SPIKE_MULTIPLIER) * 0.05, 0.82)

        signal = {
            "market_id": market["id"],
            "question": market.get("question", ""),
            "signal_type": "WHALE",
            "direction": direction,
            "confidence": round(confidence, 4),
            "edge": round(edge, 4),
            "predicted_prob": round(yes_price + edge, 4),
            "market_price": round(yes_price, 4),
            "sentiment_score": 0.0,
            "source": f"Whale/Vélocité ×{ratio:.1f} (${recent_vol:.0f} vs ${baseline_vol:.0f})",
            "market_url": market.get("market_url", ""),
            "whale_ratio": round(ratio, 2),
            "directional_pct": round(directional_pct, 2),
        }

        await self.db.save_signal(signal)
        logger.info(
            f"🐋 WHALE [{direction}] {market.get('question', '')[:55]} "
            f"| vol×{ratio:.1f} | {directional_pct:.0%} orienté {direction}"
        )
        return signal

    def stop(self):
        self._running = False
        logger.info("Agent 10 (WhaleTracker) arrêté")
