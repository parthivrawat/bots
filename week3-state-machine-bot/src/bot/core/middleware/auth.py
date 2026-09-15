"""Auth middleware: auto-register the caller, load their User, reject banned.

Registration is idempotent — get_or_create makes /start and first contact
equivalent, and repeated calls never create duplicate rows (UNIQUE constraint
on platform+platform_user_id backs this at the DB level).
"""

from __future__ import annotations

from ..contracts import HandlerContext
from ..errors import Banned


def make_auth_middleware():
    async def auth(ctx: HandlerContext) -> None:
        user = await ctx.services.users.get_or_create(
            platform=ctx.message.platform,
            platform_user_id=ctx.message.platform_user_id,
            username=ctx.message.username,
        )
        if user.is_banned:
            raise Banned()
        ctx.user = user
    return auth
