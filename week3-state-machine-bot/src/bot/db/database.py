"""SQLite via aiosqlite, with numbered migration files applied at startup.

A single connection guarded by an asyncio.Lock is fine at this scale —
SQLite serializes writes anyway. Migration files live in ./migrations and are
named NNN_description.sql; applied versions are tracked in schema_migrations.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


class Database:
    def __init__(self, path: str):
        self.path = path
        self._conn: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.commit()
        await self.migrate()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database.connect() has not been called")
        return self._conn

    @property
    def lock(self) -> asyncio.Lock:
        return self._lock

    async def migrate(self) -> None:
        await self.conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "  version INTEGER PRIMARY KEY,"
            "  applied_at TEXT NOT NULL DEFAULT (datetime('now'))"
            ")"
        )
        cur = await self.conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations")
        (applied,) = await cur.fetchone()

        files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for f in files:
            version = int(f.name.split("_", 1)[0])
            if version <= applied:
                continue
            logger.info("applying migration %s", f.name)
            async with self._lock:
                try:
                    await self.conn.executescript(f.read_text(encoding="utf-8"))
                    await self.conn.execute(
                        "INSERT INTO schema_migrations (version) VALUES (?)", (version,)
                    )
                    await self.conn.commit()
                except Exception:
                    await self.conn.rollback()
                    raise
