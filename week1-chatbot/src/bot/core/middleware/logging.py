"""Structured per-command logging."""

from __future__ import annotations

import logging

from ..contracts import HandlerContext

logger = logging.getLogger("bot.command")


async def logging_middleware(ctx: HandlerContext) -> None:
    logger.info(
        "command",
        extra={
            "platform": ctx.message.platform,
            "platform_user_id": ctx.message.platform_user_id,
            "command": ctx.command.name,
            "args": ctx.command.args,
        },
    )
