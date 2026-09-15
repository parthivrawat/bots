"""Pure text normalization for platform-specific mention/command syntax.

Keeps dependency-free so unit tests never need slack_bolt/asyncpraw installed.
"""

from __future__ import annotations

import re

_MENTION = re.compile(r"<@[A-Z0-9]+>")


def clean_slack_text(text: str) -> str:
    """Strip <@USER> mentions. Explicit /cmd or !cmd stays as-is;
    bare words are left as-is so the state middleware can capture replies."""
    return _MENTION.sub("", text).strip()


def clean_reddit_text(text: str, bot_name: str) -> str:
    """Strip u/<bot> mentions; explicit /cmd or !cmd stays as-is.
    Bare words are left as-is for state-machine replies."""
    stripped = re.sub(
        rf"u/{re.escape(bot_name)}\b", "", text, flags=re.IGNORECASE
    ).strip()
    return stripped
