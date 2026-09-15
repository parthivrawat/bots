"""Conversation-state persistence for multi-step workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from ...core.contracts import User
from ..database import Database


@dataclass
class Conversation:
    id: int
    user_id: int
    workflow: str
    state: str
    data: dict
    status: str


def _row_to_conversation(row) -> Conversation:
    return Conversation(
        id=row["id"],
        user_id=row["user_id"],
        workflow=row["workflow"],
        state=row["state"],
        data=json.loads(row["data"] or "{}"),
        status=row["status"],
    )


class StateRepository:
    def __init__(self, db: Database):
        self.db = db

    async def get_active(self, user_id: int, workflow: Optional[str] = None) -> Optional[Conversation]:
        if workflow:
            cur = await self.db.conn.execute(
                "SELECT * FROM conversation_states "
                "WHERE user_id=? AND workflow=? AND status='active'",
                (user_id, workflow),
            )
        else:
            cur = await self.db.conn.execute(
                "SELECT * FROM conversation_states "
                "WHERE user_id=? AND status='active'",
                (user_id,),
            )
        row = await cur.fetchone()
        return _row_to_conversation(row) if row else None

    async def start(self, user: User, workflow: str, initial_state: str, data: dict) -> Conversation:
        async with self.db.lock:
            cur = await self.db.conn.execute(
                "INSERT INTO conversation_states (user_id, workflow, state, data) "
                "VALUES (?, ?, ?, ?)",
                (user.id, workflow, initial_state, json.dumps(data)),
            )
            await self.db.conn.commit()
            conv_id = cur.lastrowid
        return await self.get_by_id(conv_id)

    async def get_by_id(self, conversation_id: int) -> Conversation:
        cur = await self.db.conn.execute(
            "SELECT * FROM conversation_states WHERE id=?", (conversation_id,)
        )
        row = await cur.fetchone()
        return _row_to_conversation(row)

    async def update(self, conversation_id: int, state: str, data: dict) -> None:
        async with self.db.lock:
            await self.db.conn.execute(
                "UPDATE conversation_states "
                "SET state=?, data=?, updated_at=datetime('now') "
                "WHERE id=?",
                (state, json.dumps(data), conversation_id),
            )
            await self.db.conn.commit()

    async def set_status(self, conversation_id: int, status: str) -> None:
        async with self.db.lock:
            await self.db.conn.execute(
                "UPDATE conversation_states "
                "SET status=?, updated_at=datetime('now') "
                "WHERE id=?",
                (status, conversation_id),
            )
            await self.db.conn.commit()
