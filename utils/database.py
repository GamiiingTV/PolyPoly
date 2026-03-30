"""
PolyPoly — Gestionnaire de Base de Données
SQLite async — stocke marchés, signaux, trades, apprentissage.
"""

import json
import aiosqlite
from datetime import datetime
from typing import Optional
from loguru import logger

from config import DATABASE_PATH


CREATE_TABLES_SQL = """
-- Marchés scannés
CREATE TABLE IF NOT EXISTS markets (
    id              TEXT PRIMARY KEY,
    question        TEXT NOT NULL,
    category        TEXT,
    yes_price       REAL,
    no_price        REAL,
    liquidity       REAL,
    volume_24h      REAL,
    end_date        TEXT,
    active          INTEGER DEFAULT 1,
    anomaly_score   REAL DEFAULT 0.0,
    spread          REAL DEFAULT 0.0,
    last_updated    TEXT,
    raw_data        TEXT
);

-- Signaux générés
CREATE TABLE IF NOT EXISTS signals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id       TEXT NOT NULL,
    signal_type     TEXT,               -- 'SENTIMENT', 'ANOMALY', 'PREDICTION'
    direction       TEXT,               -- 'YES' ou 'NO'
    confidence      REAL,
    edge            REAL,               -- Écart entre prob prédite et prix marché
    predicted_prob  REAL,
    market_price    REAL,
    sentiment_score REAL,
    source          TEXT,               -- Source du signal
    created_at      TEXT DEFAULT (datetime('now')),
    acted_on        INTEGER DEFAULT 0
);

-- Trades placés
CREATE TABLE IF NOT EXISTS trades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id       TEXT NOT NULL,
    order_id        TEXT,
    direction       TEXT,               -- 'YES' ou 'NO'
    size_usd        REAL,
    entry_price     REAL,
    exit_price      REAL,
    pnl             REAL,
    status          TEXT DEFAULT 'OPEN', -- 'OPEN', 'WON', 'LOST', 'CANCELLED'
    signal_id       INTEGER,
    confidence      REAL,
    edge            REAL,
    sentiment_score REAL,
    features_json   TEXT,               -- Features XGBoost au moment du trade
    error_analysis  TEXT,               -- Analyse post-mortem (Agent 5)
    placed_at       TEXT DEFAULT (datetime('now')),
    resolved_at     TEXT,
    FOREIGN KEY (signal_id) REFERENCES signals(id)
);

-- Historique des prix pour détecter anomalies
CREATE TABLE IF NOT EXISTS price_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id       TEXT NOT NULL,
    yes_price       REAL,
    no_price        REAL,
    spread          REAL,
    volume          REAL,
    recorded_at     TEXT DEFAULT (datetime('now'))
);

-- Apprentissage — Patterns d'erreurs
CREATE TABLE IF NOT EXISTS learning_patterns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type    TEXT NOT NULL,      -- 'OVERCONFIDENCE', 'SENTIMENT_TRAP', etc.
    description     TEXT,
    frequency       INTEGER DEFAULT 1,
    avg_loss        REAL,
    conditions_json TEXT,               -- Conditions qui déclenchent ce pattern
    mitigation      TEXT,               -- Action corrective
    created_at      TEXT DEFAULT (datetime('now')),
    last_seen       TEXT DEFAULT (datetime('now'))
);

-- Paramètres dynamiques mis à jour par Agent 5
CREATE TABLE IF NOT EXISTS dynamic_params (
    key             TEXT PRIMARY KEY,
    value           TEXT NOT NULL,
    updated_at      TEXT DEFAULT (datetime('now')),
    reason          TEXT
);

-- Rapport de performance
CREATE TABLE IF NOT EXISTS performance_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    total_trades    INTEGER,
    winning_trades  INTEGER,
    win_rate        REAL,
    total_pnl       REAL,
    avg_edge        REAL,
    avg_confidence  REAL,
    best_category   TEXT,
    worst_pattern   TEXT,
    snapshot_at     TEXT DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_trades_market    ON trades(market_id);
CREATE INDEX IF NOT EXISTS idx_trades_status    ON trades(status);
CREATE INDEX IF NOT EXISTS idx_signals_market   ON signals(market_id);
CREATE INDEX IF NOT EXISTS idx_price_history    ON price_history(market_id, recorded_at);
"""


class Database:
    """Gestionnaire async SQLite pour PolyPoly."""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._conn.executescript(CREATE_TABLES_SQL)
        await self._conn.commit()
        logger.info(f"Database connectée: {self.db_path}")

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()

    # ------------------------------------------------------------------ #
    # MARCHÉS
    # ------------------------------------------------------------------ #

    async def upsert_market(self, market: dict) -> None:
        sql = """
        INSERT INTO markets (id, question, category, yes_price, no_price,
            liquidity, volume_24h, end_date, active, anomaly_score, spread,
            last_updated, raw_data)
        VALUES (:id, :question, :category, :yes_price, :no_price,
            :liquidity, :volume_24h, :end_date, :active, :anomaly_score,
            :spread, :last_updated, :raw_data)
        ON CONFLICT(id) DO UPDATE SET
            yes_price=excluded.yes_price, no_price=excluded.no_price,
            liquidity=excluded.liquidity, volume_24h=excluded.volume_24h,
            end_date=excluded.end_date, active=excluded.active,
            anomaly_score=excluded.anomaly_score, spread=excluded.spread,
            last_updated=excluded.last_updated, raw_data=excluded.raw_data
        """
        await self._conn.execute(sql, {**market, "raw_data": json.dumps(market)})
        await self._conn.commit()

    async def get_active_markets(self, min_liquidity: float = 0, limit: int = 500) -> list:
        sql = """
        SELECT * FROM markets WHERE active=1 AND liquidity >= ?
        ORDER BY anomaly_score DESC, volume_24h DESC LIMIT ?
        """
        async with self._conn.execute(sql, (min_liquidity, limit)) as cur:
            rows = await cur.fetchall()
            return [self._enrich_market(dict(r)) for r in rows]

    async def get_market(self, market_id: str) -> Optional[dict]:
        async with self._conn.execute("SELECT * FROM markets WHERE id=?", (market_id,)) as cur:
            row = await cur.fetchone()
            return self._enrich_market(dict(row)) if row else None

    @staticmethod
    def _enrich_market(market: dict) -> dict:
        """
        Injecte market_url et token_id_yes/no depuis raw_data.
        Ces champs ne sont pas des colonnes DB mais sont nécessaires à tous les agents.
        """
        import json as _json
        import ast as _ast
        raw_str = market.get("raw_data", "")
        if not raw_str:
            return market
        try:
            raw = _json.loads(raw_str) if isinstance(raw_str, str) else raw_str

            # market_url depuis slug ou groupSlug
            if not market.get("market_url"):
                group_slug = raw.get("groupSlug", "") or raw.get("group_slug", "")
                slug = raw.get("slug", "")
                if group_slug:
                    market["market_url"] = f"https://polymarket.com/event/{group_slug}"
                elif slug:
                    market["market_url"] = f"https://polymarket.com/market/{slug}"

            # token_id_yes / token_id_no depuis clobTokenIds
            if not market.get("token_id_yes"):
                clob_ids = raw.get("clobTokenIds", [])
                if isinstance(clob_ids, str):
                    try:
                        clob_ids = _ast.literal_eval(clob_ids)
                    except Exception:
                        clob_ids = []
                if clob_ids:
                    market["token_id_yes"] = clob_ids[0]
                    market["token_id_no"] = clob_ids[1] if len(clob_ids) > 1 else clob_ids[0]
        except Exception:
            pass
        return market

    # ------------------------------------------------------------------ #
    # HISTORIQUE DES PRIX
    # ------------------------------------------------------------------ #

    async def record_price(self, market_id: str, yes_price: float,
                           no_price: float, spread: float, volume: float) -> None:
        sql = """
        INSERT INTO price_history (market_id, yes_price, no_price, spread, volume)
        VALUES (?, ?, ?, ?, ?)
        """
        await self._conn.execute(sql, (market_id, yes_price, no_price, spread, volume))
        await self._conn.commit()

    async def get_price_history(self, market_id: str, minutes: int = 30) -> list:
        sql = """
        SELECT * FROM price_history
        WHERE market_id=? AND recorded_at >= datetime('now', ? || ' minutes')
        ORDER BY recorded_at ASC
        """
        async with self._conn.execute(sql, (market_id, f"-{minutes}")) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    # ------------------------------------------------------------------ #
    # SIGNAUX
    # ------------------------------------------------------------------ #

    async def save_signal(self, signal: dict) -> int:
        sql = """
        INSERT INTO signals (market_id, signal_type, direction, confidence,
            edge, predicted_prob, market_price, sentiment_score, source)
        VALUES (:market_id, :signal_type, :direction, :confidence,
            :edge, :predicted_prob, :market_price, :sentiment_score, :source)
        """
        async with self._conn.execute(sql, signal) as cur:
            signal_id = cur.lastrowid
        await self._conn.commit()
        return signal_id

    async def get_recent_signals(self, limit: int = 50, hours: int = 3) -> list:
        """Retourne les signaux non-actionnés des dernières `hours` heures."""
        sql = """
        SELECT s.*, m.question FROM signals s
        JOIN markets m ON s.market_id = m.id
        WHERE s.acted_on = 0
        AND s.created_at >= datetime('now', ? || ' hours')
        ORDER BY s.created_at DESC LIMIT ?
        """
        async with self._conn.execute(sql, (f"-{hours}", limit)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_recent_signals_for_market(self, market_id: str, hours: int = 1) -> list:
        """Retourne les signaux récents pour un marché spécifique."""
        sql = """
        SELECT * FROM signals
        WHERE market_id = ?
        AND created_at >= datetime('now', ? || ' hours')
        ORDER BY created_at DESC
        """
        async with self._conn.execute(sql, (market_id, f"-{hours}")) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def mark_signal_acted_on(self, signal_id: int) -> None:
        await self._conn.execute(
            "UPDATE signals SET acted_on=1 WHERE id=?", (signal_id,)
        )
        await self._conn.commit()

    # ------------------------------------------------------------------ #
    # TRADES
    # ------------------------------------------------------------------ #

    async def save_trade(self, trade: dict) -> int:
        sql = """
        INSERT INTO trades (market_id, order_id, direction, size_usd,
            entry_price, status, signal_id, confidence, edge,
            sentiment_score, features_json)
        VALUES (:market_id, :order_id, :direction, :size_usd,
            :entry_price, :status, :signal_id, :confidence, :edge,
            :sentiment_score, :features_json)
        """
        async with self._conn.execute(sql, trade) as cur:
            trade_id = cur.lastrowid
        await self._conn.commit()
        return trade_id

    async def update_trade(self, trade_id: int, updates: dict) -> None:
        sets = ", ".join(f"{k}=?" for k in updates)
        sql = f"UPDATE trades SET {sets} WHERE id=?"
        await self._conn.execute(sql, (*updates.values(), trade_id))
        await self._conn.commit()

    async def get_open_trades(self) -> list:
        sql = """
        SELECT t.*, m.question FROM trades t
        JOIN markets m ON t.market_id = m.id
        WHERE t.status = 'OPEN'
        ORDER BY t.placed_at DESC
        """
        async with self._conn.execute(sql) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_closed_trades(self, limit: int = 200) -> list:
        sql = """
        SELECT t.*, m.question FROM trades t
        JOIN markets m ON t.market_id = m.id
        WHERE t.status IN ('WON', 'LOST')
        ORDER BY t.resolved_at DESC LIMIT ?
        """
        async with self._conn.execute(sql, (limit,)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_losing_trades(self, limit: int = 100) -> list:
        sql = """
        SELECT t.*, m.question FROM trades t
        JOIN markets m ON t.market_id = m.id
        WHERE t.status = 'LOST'
        ORDER BY t.pnl ASC LIMIT ?
        """
        async with self._conn.execute(sql, (limit,)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_trade_stats(self) -> dict:
        sql = """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status='WON' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN status='LOST' THEN 1 ELSE 0 END) as losses,
            SUM(COALESCE(pnl, 0)) as total_pnl,
            AVG(CASE WHEN status IN ('WON','LOST') THEN COALESCE(pnl, 0) END) as avg_pnl,
            AVG(confidence) as avg_confidence,
            AVG(edge) as avg_edge
        FROM trades WHERE status IN ('WON', 'LOST')
        """
        async with self._conn.execute(sql) as cur:
            row = await cur.fetchone()
            d = dict(row) if row else {}
            d["win_rate"] = (d.get("wins", 0) / d["total"] * 100) if d.get("total", 0) > 0 else 0
            return d

    # ------------------------------------------------------------------ #
    # APPRENTISSAGE
    # ------------------------------------------------------------------ #

    async def save_learning_pattern(self, pattern: dict) -> None:
        sql = """
        INSERT INTO learning_patterns (pattern_type, description, avg_loss,
            conditions_json, mitigation)
        VALUES (:pattern_type, :description, :avg_loss, :conditions_json, :mitigation)
        ON CONFLICT DO NOTHING
        """
        await self._conn.execute(sql, pattern)
        await self._conn.commit()

    async def get_learning_patterns(self) -> list:
        sql = "SELECT * FROM learning_patterns ORDER BY frequency DESC, avg_loss ASC"
        async with self._conn.execute(sql) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def increment_pattern(self, pattern_type: str) -> None:
        sql = """
        UPDATE learning_patterns
        SET frequency = frequency + 1, last_seen = datetime('now')
        WHERE pattern_type = ?
        """
        await self._conn.execute(sql, (pattern_type,))
        await self._conn.commit()

    # ------------------------------------------------------------------ #
    # PARAMÈTRES DYNAMIQUES
    # ------------------------------------------------------------------ #

    async def get_param(self, key: str, default=None):
        sql = "SELECT value FROM dynamic_params WHERE key=?"
        async with self._conn.execute(sql, (key,)) as cur:
            row = await cur.fetchone()
            return json.loads(row["value"]) if row else default

    async def set_param(self, key: str, value, reason: str = "") -> None:
        sql = """
        INSERT INTO dynamic_params (key, value, updated_at, reason)
        VALUES (?, ?, datetime('now'), ?)
        ON CONFLICT(key) DO UPDATE SET
            value=excluded.value, updated_at=excluded.updated_at, reason=excluded.reason
        """
        await self._conn.execute(sql, (key, json.dumps(value), reason))
        await self._conn.commit()

    # ------------------------------------------------------------------ #
    # SNAPSHOTS PERFORMANCE
    # ------------------------------------------------------------------ #

    async def save_performance_snapshot(self, snap: dict) -> None:
        sql = """
        INSERT INTO performance_snapshots
            (total_trades, winning_trades, win_rate, total_pnl, avg_edge,
             avg_confidence, best_category, worst_pattern)
        VALUES (:total_trades, :winning_trades, :win_rate, :total_pnl,
            :avg_edge, :avg_confidence, :best_category, :worst_pattern)
        """
        await self._conn.execute(sql, snap)
        await self._conn.commit()
