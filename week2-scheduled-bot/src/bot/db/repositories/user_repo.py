"""User persistence: registration, settings, roles. All queries parameterized."""

from __future__ import annotations

from typing import Optional

from ...core.contracts import User
from ..database import Database


def _row_to_user(row) -> User:
    return User(
        id=row["id"], platform=row["platform"],
        platform_user_id=row["platform_user_id"], username=row["username"],
        role=row["role"], locale=row["locale"],
        created_at=row["created_at"], last_seen_at=row["last_seen_at"],
    )


class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    async def get_or_create(self, platform: str, platform_user_id: str,
                            username: Optional[str]) -> User:
        async with self.db.lock:
            cur = await self.db.conn.execute(
                "SELECT * FROM users WHERE platform=? AND platform_user_id=?",
                (platform, platform_user_id),
            )
            row = await cur.fetchone()
            if row is None:
                cur = await self.db.conn.execute(
                    "INSERT INTO users (platform, platform_user_id, username)"
                    " VALUES (?, ?, ?)",
                    (platform, platform_user_id, username),
                )
                uid = cur.lastrowid
            else:
                uid = row["id"]
            # idempotent touch: username + last_seen always refreshed
            await self.db.conn.execute(
                "UPDATE users SET last_seen_at=datetime('now'),"
                "    username=COALESCE(?, username) WHERE id=?",
                (username, uid),
            )
            await self.db.conn.commit()
            cur = await self.db.conn.execute("SELECT * FROM users WHERE id=?", (uid,))
            return _row_to_user(await cur.fetchone())

    async def get(self, platform: str, platform_user_id: str) -> Optional[User]:
        cur = await self.db.conn.execute(
            "SELECT * FROM users WHERE platform=? AND platform_user_id=?",
            (platform, platform_user_id),
        )
        row = await cur.fetchone()
        return _row_to_user(row) if row else None

    async def set_role(self, platform: str, platform_user_id: str, role: str) -> bool:
        async with self.db.lock:
            cur = await self.db.conn.execute(
                "UPDATE users SET role=? WHERE platform=? AND platform_user_id=?",
                (role, platform, platform_user_id),
            )
            await self.db.conn.commit()
            return cur.rowcount > 0

    async def set_setting(self, user_id: int, key: str, value: str) -> None:
        async with self.db.lock:
            await self.db.conn.execute(
                "INSERT INTO user_settings (user_id, key, value) VALUES (?, ?, ?)"
                " ON CONFLICT (user_id, key) DO UPDATE SET value=excluded.value",
                (user_id, key, value),
            )
            await self.db.conn.commit()

    async def get_settings(self, user_id: int) -> dict[str, str]:
        cur = await self.db.conn.execute(
            "SELECT key, value FROM user_settings WHERE user_id=? ORDER BY key",
            (user_id,),
        )
        return {r["key"]: r["value"] for r in await cur.fetchall()}

    async def count(self) -> int:
        cur = await self.db.conn.execute("SELECT COUNT(*) FROM users")
        (n,) = await cur.fetchone()
        return n

    async def count_by_platform(self) -> dict[str, int]:
        cur = await self.db.conn.execute(
            "SELECT platform, COUNT(*) AS n FROM users GROUP BY platform"
        )
        return {r["platform"]: r["n"] for r in await cur.fetchall()}

    async def get_setting(self, user_id: int, key: str, default: str | None = None) -> str | None:
        """Get a single setting value."""
        cur = await self.db.conn.execute(
            "SELECT value FROM user_settings WHERE user_id=? AND key=?",
            (user_id, key),
        )
        row = await cur.fetchone()
        return row["value"] if row else default

    async def get_users_with_setting(self, key: str, value: str) -> list[User]:
        """Get all users who have a specific setting value."""
        cur = await self.db.conn.execute(
            """
            SELECT u.* FROM users u
            JOIN user_settings s ON u.id = s.user_id
            WHERE s.key = ? AND s.value = ?
            """,
            (key, value),
        )
        rows = await cur.fetchall()
        return [self._row_to_user(row) for row in rows]

    async def get_admins(self) -> list[User]:
        """Get all admin users."""
        cur = await self.db.conn.execute(
            "SELECT * FROM users WHERE role = 'admin'"
        )
        rows = await cur.fetchall()
        return [self._row_to_user(row) for row in rows]
