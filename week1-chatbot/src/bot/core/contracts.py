"""Platform-neutral contracts shared by adapters, router, and handlers.

Nothing in core/ may import telegram or discord — adapters translate platform
events into IncomingMessage and translate OutgoingReply back.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class IncomingMessage:
    platform: str                    # "telegram" | "discord" | "eval"
    platform_user_id: str
    username: Optional[str]
    text: str                        # raw text, e.g. "/settings timezone=UTC"
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class OutgoingReply:
    text: str
    buttons: Optional[list[dict]] = None


@dataclass
class Command:
    """Parsed user input: `/settings tz=UTC extra` -> name=settings,
    args=["extra"], kwargs={"tz": "UTC"}."""
    name: str
    args: list[str] = field(default_factory=list)
    kwargs: dict[str, str] = field(default_factory=dict)


@dataclass
class User:
    id: int
    platform: str
    platform_user_id: str
    username: Optional[str]
    role: str                        # "user" | "admin" | "banned"
    locale: str = "en"
    created_at: str = ""
    last_seen_at: str = ""

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_banned(self) -> bool:
        return self.role == "banned"


@dataclass
class HandlerContext:
    """Everything a handler needs: the caller, parsed command, services, config."""
    user: User
    message: IncomingMessage
    command: Command
    services: Any                    # ServiceRegistry
    settings: Any                    # AppSettings
