"""Admin operations: stats, ban/unban, broadcast stub."""

from __future__ import annotations

import logging

from ..core.errors import ValidationError
from ..db.repositories import AuditRepository, UserRepository

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, users: UserRepository, audit: AuditRepository):
        self.users = users
        self.audit = audit

    async def stats_text(self) -> str:
        total = await self.users.count()
        per_platform = await self.users.count_by_platform()
        commands_today = await self.audit.count_today()
        breakdown = ", ".join(f"{p}={n}" for p, n in per_platform.items()) or "none"
        return (
            "Bot stats\n"
            f"  Total users:      {total}\n"
            f"  By platform:      {breakdown}\n"
            f"  Commands today:   {commands_today}"
        )

    async def ban(self, target: str) -> str:
        platform, _, uid = target.partition(":")
        if not platform or not uid:
            raise ValidationError("Usage: /admin ban <platform>:<user_id>")
        ok = await self.users.set_role(platform, uid, "banned")
        if not ok:
            raise ValidationError(f"No such user: {target}")
        return f"User {target} banned."

    async def unban(self, target: str) -> str:
        platform, _, uid = target.partition(":")
        if not platform or not uid:
            raise ValidationError("Usage: /admin unban <platform>:<user_id>")
        ok = await self.users.set_role(platform, uid, "user")
        if not ok:
            raise ValidationError(f"No such user: {target}")
        return f"User {target} unbanned."

    async def broadcast(self, text: str) -> str:
        # Week 1: stub. Real fan-out needs a queue + per-platform rate limits
        # and arrives with the scheduled-jobs work in Week 2.
        if not text.strip():
            raise ValidationError("Usage: /admin broadcast <message>")
        logger.info("broadcast requested (stub): %r", text)
        return "Broadcast queued (stub — delivery lands in Week 2)."
