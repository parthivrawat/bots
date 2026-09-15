"""Audit log persistence — every command attempt, success or denial."""

from __future__ import annotations

from typing import Optional

from ..database import Database


class AuditRepository:
    def __init__(self, db: Database):
        self.db = db

    async def log(self, *, user_id: Optional[int], command: str, args: str,
                  result: str, platform: str, platform_user_id: str) -> None:
        async with self.db.lock:
            await self.db.conn.execute(
                "INSERT INTO audit_log"
                " (user_id, platform, platform_user_id, command, args, result)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, platform, platform_user_id, command, args, result),
            )
            await self.db.conn.commit()

    async def count_today(self) -> int:
        cur = await self.db.conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE date(created_at)=date('now')"
        )
        (n,) = await cur.fetchone()
        return n
