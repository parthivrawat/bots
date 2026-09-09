"""Entry point: build the app once, start whichever adapters have tokens.

    python -m bot.main
"""

from __future__ import annotations

import asyncio
import logging
import signal

from .adapters.discord_bot import DiscordAdapter
from .adapters.telegram_bot import TelegramAdapter
from .app import build_app
from .config import AppSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


async def amain() -> None:
    settings = AppSettings.from_env()
    if not settings.telegram_token and not settings.discord_token:
        raise SystemExit("Set TELEGRAM_TOKEN and/or DISCORD_TOKEN in .env")

    app = await build_app(settings)
    adapters = []
    if settings.telegram_token:
        adapters.append(TelegramAdapter(app, settings.telegram_token))
    if settings.discord_token:
        adapters.append(DiscordAdapter(app, settings.discord_token))

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass  # Windows: fall back to KeyboardInterrupt

    for a in adapters:
        await a.start()
    logger.info("Bot running with %d adapter(s); Ctrl+C to stop", len(adapters))

    try:
        await stop.wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        for a in adapters:
            try:
                await a.stop()
            except Exception:
                logger.exception("adapter stop failed")
        await app.close()


if __name__ == "__main__":
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass
