"""Entry point: build the app once, start whichever adapters have tokens.

    python -m bot.main
"""

from __future__ import annotations

import asyncio
import json
import logging
import signal

from .adapters.discord_bot import DiscordAdapter
from .adapters.reddit_bot import RedditAdapter
from .adapters.slack_bot import SlackAdapter
from .adapters.telegram_bot import TelegramAdapter
from .app import build_app
from .config import AppSettings


class JSONFormatter(logging.Formatter):
    """JSON-lines formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "platform"):
            log_obj["platform"] = record.platform
        if hasattr(record, "platform_user_id"):
            log_obj["platform_user_id"] = record.platform_user_id
        if hasattr(record, "command"):
            log_obj["command"] = record.command
        if hasattr(record, "args"):
            log_obj["args"] = record.args
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(
    level=logging.INFO,
    handlers=[handler],
)
logger = logging.getLogger(__name__)


async def amain() -> None:
    settings = AppSettings.from_env()
    has_reddit = all([
        settings.reddit_client_id, settings.reddit_client_secret,
        settings.reddit_username, settings.reddit_password,
        settings.reddit_user_agent,
    ])
    has_slack = settings.slack_bot_token and settings.slack_app_token
    if not any([settings.telegram_token, settings.discord_token, has_slack, has_reddit]):
        raise SystemExit(
            "No platform configured — set TELEGRAM_TOKEN, DISCORD_TOKEN, "
            "SLACK_BOT_TOKEN+SLACK_APP_TOKEN, or the REDDIT_* vars in .env"
        )

    app = await build_app(settings)
    adapters = []
    app.adapters = adapters
    if settings.telegram_token:
        adapters.append(TelegramAdapter(app, settings.telegram_token))
    if settings.discord_token:
        adapters.append(DiscordAdapter(app, settings.discord_token))
    if has_slack:
        adapters.append(SlackAdapter(app, settings.slack_bot_token, settings.slack_app_token))
    if has_reddit:
        adapters.append(RedditAdapter(
            app,
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            username=settings.reddit_username,
            password=settings.reddit_password,
            user_agent=settings.reddit_user_agent,
        ))

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass  # Windows: fall back to KeyboardInterrupt

    # Start adapters
    for a in adapters:
        await a.start()
    
    # Start scheduler (Week 2)
    if app.scheduler:
        await app.scheduler.start()
        logger.info("Bot running with %d adapter(s) + scheduler; Ctrl+C to stop", len(adapters))
    else:
        logger.info("Bot running with %d adapter(s); Ctrl+C to stop", len(adapters))

    try:
        await stop.wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        # Stop scheduler first (wait for running jobs)
        if app.scheduler:
            logger.info("Stopping scheduler...")
            await app.scheduler.stop()
        
        # Then stop adapters
        for a in adapters:
            try:
                await a.stop()
            except Exception:
                logger.exception("adapter stop failed")
        
        # Finally close app (database, etc.)
        await app.close()


if __name__ == "__main__":
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass
