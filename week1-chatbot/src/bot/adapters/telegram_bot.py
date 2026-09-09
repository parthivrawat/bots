"""Telegram adapter via python-telegram-bot (v21+, async API).

All platform specifics live here: Update -> IncomingMessage, OutgoingReply ->
send_message. The core never sees a telegram object.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from ..app import App
from ..core.contracts import IncomingMessage

logger = logging.getLogger(__name__)


class TelegramAdapter:
    def __init__(self, app: App, token: str):
        self.app = app
        self.ptb = (
            Application.builder()
            .token(token)
            .build()
        )
        # Route ALL text through our router — commands and plain text alike.
        self.ptb.add_handler(
            MessageHandler(filters.TEXT & ~filters.StatusUpdate.ALL, self._on_message)
        )

    async def _on_message(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.effective_user:
            return
        msg = IncomingMessage(
            platform="telegram",
            platform_user_id=str(update.effective_user.id),
            username=update.effective_user.username,
            text=update.message.text or "",
            context={"chat_id": update.effective_chat.id if update.effective_chat else None},
        )
        reply = await self.app.router.dispatch(msg)
        await update.message.reply_text(reply.text)

    async def start(self) -> None:
        await self.ptb.initialize()
        await self.ptb.start()
        await self.ptb.updater.start_polling()
        logger.info("Telegram adapter polling")

    async def stop(self) -> None:
        await self.ptb.updater.stop()
        await self.ptb.stop()
        await self.ptb.shutdown()
