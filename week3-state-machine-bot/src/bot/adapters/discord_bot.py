"""Discord adapter via discord.py (v2+).

Requires the 'Message Content' privileged intent enabled in the Discord
Developer Portal — otherwise on_message sees empty text.
"""

from __future__ import annotations

import asyncio
import logging

import discord

from ..app import App
from ..core.contracts import IncomingMessage, User

logger = logging.getLogger(__name__)


class DiscordAdapter:
    platform = "discord"

    def __init__(self, app: App, token: str):
        self.app = app
        self.token = token
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        self._ready = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._register_events()

    def _register_events(self) -> None:
        @self.client.event
        async def on_ready():
            self._ready.set()
            logger.info("Discord adapter ready as %s", self.client.user)

        @self.client.event
        async def on_message(message: discord.Message):
            if message.author.bot:
                return
            text = message.content.strip()
            if not text:
                return
            msg = IncomingMessage(
                platform="discord",
                platform_user_id=str(message.author.id),
                username=message.author.name,
                text=text,
                context={"channel_id": message.channel.id,
                         "guild_id": message.guild.id if message.guild else None},
            )
            reply = await self.app.router.dispatch(msg)
            await message.channel.send(reply.text)

    async def start(self) -> None:
        self._ready.clear()
        self._task = asyncio.create_task(self.client.start(self.token))

        ready_task = asyncio.create_task(self._ready.wait())
        done, _ = await asyncio.wait(
            [self._task, ready_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        if self._task in done:
            # client.start finished before on_ready — likely a startup error
            exc = self._task.exception()
            if exc:
                raise exc

    async def stop(self) -> None:
        await self.client.close()
        if self._task:
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def send(self, user: User, message: str) -> None:
        target = await self.client.fetch_user(int(user.platform_user_id))
        if target:
            await target.send(message)
