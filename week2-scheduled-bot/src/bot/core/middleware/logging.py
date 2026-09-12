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
            "command": ctx.command.name,
        },
    )
