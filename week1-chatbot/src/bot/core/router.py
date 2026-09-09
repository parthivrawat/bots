"""Router: parse -> middleware -> dispatch -> audit -> reply.

Handlers are async callables (HandlerContext) -> str. Register them with
metadata; the router enforces admin gating and converts domain errors into
replies so handlers never format error text themselves.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from .contracts import Command, HandlerContext, IncomingMessage, OutgoingReply
from .errors import BotError, PermissionDenied, UnknownCommand

logger = logging.getLogger(__name__)

Handler = Callable[[HandlerContext], Awaitable[str]]
Middleware = Callable[[HandlerContext], Awaitable[None]]

_KV = re.compile(r"^([A-Za-z_][\w.-]*)=(.*)$", re.DOTALL)


@dataclass
class CommandSpec:
    name: str
    handler: Handler
    help_text: str
    admin_only: bool = False


@dataclass
class Router:
    services: Any                    # ServiceRegistry
    settings: Any                    # AppSettings
    commands: dict[str, CommandSpec] = field(default_factory=dict)
    middleware: list[Middleware] = field(default_factory=list)

    def register(self, name: str, help_text: str, *, admin_only: bool = False):
        def deco(fn: Handler) -> Handler:
            self.commands[name] = CommandSpec(name, fn, help_text, admin_only)
            return fn
        return deco

    # -- parsing -----------------------------------------------------------

    @staticmethod
    def parse(text: str) -> Command:
        text = text.strip()
        if text.startswith("/") or text.startswith("!"):
            text = text[1:]
        if not text:
            raise UnknownCommand()
        head, *rest = text.split(maxsplit=1)
        name = head.split("@", 1)[0].lower()           # strip /cmd@BotName
        tokens = rest[0].split() if rest else []
        args, kwargs = [], {}
        for tok in tokens:
            m = _KV.match(tok)
            if m:
                kwargs[m.group(1).lower()] = m.group(2)
            else:
                args.append(tok)
        return Command(name=name, args=args, kwargs=kwargs)

    # -- dispatch ----------------------------------------------------------

    async def dispatch(self, msg: IncomingMessage) -> OutgoingReply:
        result = "ok"
        ctx: HandlerContext | None = None
        try:
            cmd = self.parse(msg.text)
            ctx = HandlerContext(
                user=None, message=msg, command=cmd,   # user filled by auth mw
                services=self.services, settings=self.settings,
            )
            for mw in self.middleware:
                await mw(ctx)

            spec = self.commands.get(cmd.name)
            if spec is None:
                raise UnknownCommand()
            if spec.admin_only and not (ctx.user and ctx.user.is_admin):
                result = "denied"
                raise PermissionDenied()

            text = await spec.handler(ctx)
            return OutgoingReply(text=text)

        except BotError as exc:
            if result == "ok":
                result = "denied" if isinstance(exc, PermissionDenied) else "error"
            return OutgoingReply(text=exc.user_message)
        except Exception:
            logger.exception("Unhandled error in command %r", msg.text)
            result = "error"
            return OutgoingReply(text=BotError.user_message)
        finally:
            if self.services is not None:
                try:
                    user_id = ctx.user.id if ctx and ctx.user else None
                    await self.services.audit.log(
                        user_id=user_id,
                        command=msg.text.strip().split(maxsplit=1)[0] if msg.text else "",
                        args=msg.text.strip(),
                        result=result,
                        platform=msg.platform,
                        platform_user_id=msg.platform_user_id,
                    )
                except Exception:
                    logger.exception("audit log write failed")

    # -- introspection for /help -------------------------------------------

    def visible_commands(self, is_admin: bool) -> list[CommandSpec]:
        return [
            s for s in self.commands.values()
            if is_admin or not s.admin_only
        ]
