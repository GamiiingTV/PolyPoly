"""O.R.A.C.L.E — SQLite-backed knowledge store"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import aiosqlite
from loguru import logger

from ..models.schemas import Discovery, KnowledgeEntry

# Resolves to oracle/oracle.db regardless of OS or working directory
DB_PATH = str(Path(__file__).parent.parent.parent / "oracle.db")


class KnowledgeBase:
    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self):
        """Create tables if they do not exist and open persistent connection."""
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row

        await self._db.execute("PRAGMA journal_mode=WAL;")
        await self._db.execute("PRAGMA foreign_keys=ON;")

        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_entries (
                id            TEXT PRIMARY KEY,
                title         TEXT NOT NULL,
                content       TEXT NOT NULL,
                author_agent  TEXT NOT NULL,
                author_emoji  TEXT NOT NULL,
                tags          TEXT NOT NULL DEFAULT '[]',
                importance    INTEGER NOT NULL DEFAULT 5,
                timestamp     TEXT NOT NULL
            )
            """
        )

        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS discoveries (
                id               TEXT PRIMARY KEY,
                title            TEXT NOT NULL,
                description      TEXT NOT NULL,
                agents_involved  TEXT NOT NULL DEFAULT '[]',
                breakthrough_level INTEGER NOT NULL DEFAULT 5,
                timestamp        TEXT NOT NULL
            )
            """
        )

        await self._db.commit()
        logger.info(f"KnowledgeBase initialized at {self._db_path}")

    async def close(self):
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    # ------------------------------------------------------------------
    # Knowledge entries
    # ------------------------------------------------------------------

    async def add_entry(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        """Persist a KnowledgeEntry and return it."""
        await self._db.execute(
            """
            INSERT INTO knowledge_entries
                (id, title, content, author_agent, author_emoji, tags, importance, timestamp)
            VALUES
                (:id, :title, :content, :author_agent, :author_emoji, :tags, :importance, :timestamp)
            """,
            {
                "id": entry.id,
                "title": entry.title,
                "content": entry.content,
                "author_agent": entry.author_agent,
                "author_emoji": entry.author_emoji,
                "tags": json.dumps(entry.tags),
                "importance": entry.importance,
                "timestamp": entry.timestamp,
            },
        )
        await self._db.commit()
        logger.debug(f"Knowledge entry added: {entry.id} — {entry.title!r}")
        return entry

    async def get_entries(
        self,
        tags: Optional[list[str]] = None,
        author: Optional[str] = None,
        limit: int = 10,
        min_importance: int = 0,
    ) -> list[KnowledgeEntry]:
        """
        Retrieve knowledge entries filtered by optional tags, author, and
        minimum importance, ordered by importance DESC then timestamp DESC.
        """
        conditions: list[str] = ["importance >= :min_importance"]
        params: dict = {"min_importance": min_importance, "limit": limit}

        if author:
            conditions.append("author_agent = :author")
            params["author"] = author

        where = " AND ".join(conditions)
        query = (
            f"SELECT * FROM knowledge_entries WHERE {where} "
            f"ORDER BY importance DESC, timestamp DESC LIMIT :limit"
        )

        async with self._db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

        entries: list[KnowledgeEntry] = []
        for row in rows:
            entry = KnowledgeEntry(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                author_agent=row["author_agent"],
                author_emoji=row["author_emoji"],
                tags=json.loads(row["tags"]),
                importance=row["importance"],
                timestamp=row["timestamp"],
            )
            # Post-filter by tags (SQLite JSON support is optional; filter in Python)
            if tags:
                entry_tags_lower = [t.lower() for t in entry.tags]
                if not any(t.lower() in entry_tags_lower for t in tags):
                    continue
            entries.append(entry)

        return entries

    # ------------------------------------------------------------------
    # Discoveries
    # ------------------------------------------------------------------

    async def add_discovery(self, discovery: Discovery) -> Discovery:
        """Persist a Discovery and return it."""
        await self._db.execute(
            """
            INSERT INTO discoveries
                (id, title, description, agents_involved, breakthrough_level, timestamp)
            VALUES
                (:id, :title, :description, :agents_involved, :breakthrough_level, :timestamp)
            """,
            {
                "id": discovery.id,
                "title": discovery.title,
                "description": discovery.description,
                "agents_involved": json.dumps(discovery.agents_involved),
                "breakthrough_level": discovery.breakthrough_level,
                "timestamp": discovery.timestamp,
            },
        )
        await self._db.commit()
        logger.debug(f"Discovery added: {discovery.id} — {discovery.title!r}")
        return discovery

    async def get_discoveries(self, limit: int = 20) -> list[Discovery]:
        """Return discoveries ordered by breakthrough_level DESC, timestamp DESC."""
        async with self._db.execute(
            """
            SELECT * FROM discoveries
            ORDER BY breakthrough_level DESC, timestamp DESC
            LIMIT :limit
            """,
            {"limit": limit},
        ) as cursor:
            rows = await cursor.fetchall()

        return [
            Discovery(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                agents_involved=json.loads(row["agents_involved"]),
                breakthrough_level=row["breakthrough_level"],
                timestamp=row["timestamp"],
            )
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    async def get_stats(self) -> dict:
        """Return aggregate statistics for the knowledge base."""
        async with self._db.execute(
            "SELECT COUNT(*) AS cnt FROM knowledge_entries"
        ) as cursor:
            row = await cursor.fetchone()
            total_entries = row["cnt"] if row else 0

        async with self._db.execute(
            "SELECT COUNT(*) AS cnt FROM discoveries"
        ) as cursor:
            row = await cursor.fetchone()
            total_discoveries = row["cnt"] if row else 0

        return {
            "total_entries": total_entries,
            "total_discoveries": total_discoveries,
        }
