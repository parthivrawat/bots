"""Slack adapter via slack-bolt in Socket Mode.

Socket Mode avoids needing a public webhook URL — ideal for dev and small
deployments. Requires TWO tokens:
  - SLACK_BOT_TOKEN (xoxb-...)   bot token, scopes: app_mentions:read,
                                 chat:write, im:history, im:read
  - SLACK_APP_TOKEN (xapp-...)   app-level token, scope: connections:write

Interaction model: the bot responds to @mentions in channels and to direct
messages. Text like "@Bot /profile" is normalized to "/profile"; bare words
like "help" become "/help".
"""

from __future__ import annotations

import asyncio
import logging

from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp

from ..app import App
from ..core.contracts import IncomingMessage
from .normalize import clean_slack_text

logger = logging.getLogger(__name__)


class SlackAdapter:
    def __init__(self, app: App, bot_token: str, app_token: str):
        self.app = app
        self.app_token = app_token
        self.bolt = AsyncApp(token=bot_token)
        self._handler: AsyncSocketModeHandler | None = None
        self._task: asyncio.Task | None = None
        self._register_events()

    def _register_events(self) -> None:
        @self.bolt.event("app_mention")
        async def on_mention(event, say):
            await self._handle(event, say)

        @self.bolt.event("message")
        async def on_message(event, say):
            # Only DMs — channel traffic without a mention is ignored
            if event.get("channel_type") == "im":
                await self._handle(event, say)

    async def _handle(self, event: dict, say) -> None:
        if event.get("bot_id") or event.get("subtype"):
            return  # ignore bots, edits, joins, etc.
        text = clean_slack_text(event.get("text", ""))
        msg = IncomingMessage(
            platform="slack",
            platform_user_id=event.get("user", "unknown"),
            username=None,  # enrich via users.info if needed later
            text=text,
            context={
                "channel": event.get("channel"),
                "channel_type": event.get("channel_type"),
                "team": event.get("team"),
            },
        )
        reply = await self.app.router.dispatch(msg)
        await say(text=reply.text, thread_ts=event.get("ts"))

    async def start(self) -> None:
        self._handler = AsyncSocketModeHandler(self.bolt, self.app_token)
        # start_async() blocks for the life of the socket — run it as a task
        self._task = asyncio.create_task(self._handler.start_async())
        logger.info("Slack adapter connected via Socket Mode")

    async def stop(self) -> None:
        if self._handler:
            try:
                await self._handler.client.disconnect()
            except Exception:
                logger.exception("Slack disconnect failed")
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
