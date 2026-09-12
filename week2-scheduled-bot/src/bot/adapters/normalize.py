"""Pure text normalization for platform-specific mention/command syntax.

Kept dependency-free so unit tests never need slack_bolt/asyncpraw installed.
"""

from __future__ import annotations

import re

_MENTION = re.compile(r"<@[A-Z0-9]+>")


def _to_command(text: str) -> str:
    if not text:
        return "/help"
    if not text.startswith(("/", "!")):
        text = "/" + text
    return text


def clean_slack_text(text: str) -> str:
    """Strip <@USER> mentions; "@Bot /profile" -> "/profile", "help" -> "/help"."""
    return _to_command(_MENTION.sub("", text).strip())


def clean_reddit_text(text: str, bot_name: str) -> str:
    """Strip u/<bot> mentions; "u/mybot /help" -> "/help"."""
    stripped = re.sub(
        rf"u/{re.escape(bot_name)}\b", "", text, flags=re.IGNORECASE
    ).strip()
    return _to_command(stripped)
