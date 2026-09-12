"""Reddit adapter via asyncpraw.

Interaction model differs from chat platforms: the bot responds to
  1. Username mentions   — "u/mybot /help" inside a comment
  2. Private messages    — any DM whose body starts with / or !
  3. Comment replies     — replies to the bot's own comments

Requires a Reddit "script" app (reddit.com/prefs/apps):
  REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD,
  REDDIT_USER_AGENT (e.g. "week2-scheduled-bot/0.2 by u/you")
"""

from __future__ import annotations

import asyncio
import logging

import asyncpraw
from asyncpraw.models import Comment, Message

from ..app import App
from ..core.contracts import IncomingMessage, User
from .normalize import clean_reddit_text

logger = logging.getLogger(__name__)


class RedditAdapter:
    platform = "reddit"

    def __init__(self, app: App, *, client_id: str, client_secret: str,
                 username: str, password: str, user_agent: str):
        self.app = app
        self.username = username
        self.reddit = asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent=user_agent,
        )
        self._task: asyncio.Task | None = None

    async def _handle(self, item) -> None:
        author = getattr(item, "author", None)
        if author is None or author.name.lower() == self.username.lower():
            return  # never reply to ourselves
        text = clean_reddit_text(getattr(item, "body", ""), self.username)
        msg = IncomingMessage(
            platform="reddit",
            platform_user_id=author.name,
            username=author.name,
            text=text,
            context={
                "kind": "comment" if isinstance(item, Comment) else "message",
                "subreddit": str(getattr(item, "subreddit", "")) or None,
                "permalink": getattr(item, "permalink", None),
            },
        )
        reply = await self.app.router.dispatch(msg)
        try:
            await item.reply(reply.text)
            await self.reddit.inbox.mark_read([item])
        except Exception:
            logger.exception("reddit reply failed")

    async def _inbox_loop(self) -> None:
        logger.info("Reddit adapter watching inbox")
        try:
            async for item in self.reddit.inbox.stream(skip_existing=True):
                if isinstance(item, (Comment, Message)):
                    await self._handle(item)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("reddit inbox stream died; restarting in 30s")
            await asyncio.sleep(30)
            self._task = asyncio.create_task(self._inbox_loop())

    async def start(self) -> None:
        # Verify credentials early — fails fast on bad config
        me = await self.reddit.user.me()
        logger.info("Reddit adapter authenticated as u/%s", me)
        self._task = asyncio.create_task(self._inbox_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self.reddit.close()

    async def send(self, user: User, message: str) -> None:
        redditor = await self.reddit.redditor(user.platform_user_id)
        await redditor.message(subject="Notification", message=message)
