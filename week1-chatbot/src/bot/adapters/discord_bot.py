"""Discord adapter via discord.py (v2+).

Requires the 'Message Content' privileged intent enabled in the Discord
Developer Portal — otherwise on_message sees empty text.
"""

from __future__ import annotations

import logging

import discord

from ..app import App
from ..core.contracts import IncomingMessage

logger = logging.getLogger(__name__)


class DiscordAdapter:
    def __init__(self, app: App, token: str):
        self.app = app
        self.token = token
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        self._register_events()

    def _register_events(self) -> None:
        @self.client.event
        async def on_ready():
            logger.info("Discord adapter ready as %s", self.client.user)

        @self.client.event
        async def on_message(message: discord.Message):
            if message.author.bot:
                return
            text = message.content.strip()
            if not (text.startswith("/") or text.startswith("!")):
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
        await self.client.start(self.token)

    async def stop(self) -> None:
        await self.client.close()
