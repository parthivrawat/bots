"""Eval adapter: exposes the core router to the E:\\Bots\\evals framework.

The eval framework expects a sync callable (message, context) -> BotResponse.
Our core is async, so this adapter owns a dedicated event loop in a background
thread; the app is BUILT on that loop and every dispatch runs there — required
because asyncio primitives and aiosqlite bind to the loop that first uses them.

Usage (as an evals --target):
    from bot.adapters.eval_adapter import make_eval_target
    bot = make_eval_target()            # -> framework-compatible callable
"""

from __future__ import annotations

import asyncio
import sys
import threading
from pathlib import Path
from typing import Any

# evals framework lives at ../../evals relative to this repo's parent
_EVALS_DIR = Path(__file__).resolve().parents[4] / "evals"
if _EVALS_DIR.is_dir():
    sys.path.insert(0, str(_EVALS_DIR))

from framework import BotResponse  # noqa: E402

from ..app import App, build_app  # noqa: E402
from ..config import AppSettings  # noqa: E402
from ..core.contracts import IncomingMessage  # noqa: E402


class EvalAdapter:
    def __init__(self, settings: AppSettings):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        fut = asyncio.run_coroutine_threadsafe(build_app(settings), self._loop)
        self.app: App = fut.result(timeout=30)

    def as_callable(self):
        def bot(message: str, context: dict[str, Any]) -> BotResponse:
            msg = IncomingMessage(
                platform="eval",
                platform_user_id=str(context.get("platform_user_id", "eval-user")),
                username=context.get("username", "eval"),
                text=message,
                context=context,
            )
            fut = asyncio.run_coroutine_threadsafe(
                self.app.router.dispatch(msg), self._loop
            )
            reply = fut.result(timeout=30)
            return BotResponse(
                text=reply.text,
                metadata={"refused": self._looks_refused(reply.text)},
            )
        return bot

    @staticmethod
    def _looks_refused(text: str) -> bool:
        t = text.lower()
        return "permission" in t or "revoked" in t or "can't" in t or "unknown setting" in t

    def close(self) -> None:
        fut = asyncio.run_coroutine_threadsafe(self.app.close(), self._loop)
        fut.result(timeout=10)
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)


# -- framework --target entry point ------------------------------------------

_adapter: EvalAdapter | None = None


def bot(message: str, context: dict[str, Any]) -> BotResponse:
    """Lazily builds the app on first call so `run_evals.py --target
    bot.adapters.eval_adapter:bot` works without extra setup."""
    global _adapter
    if _adapter is None:
        # Eval runs many commands rapidly as one user — give the harness a
        # high rate-limit budget so it tests handlers, not the limiter.
        _adapter = EvalAdapter(AppSettings(
            db_path=":memory:",
            rate_limit_capacity=10_000,
            rate_limit_window_s=1.0,
        ))
    return _adapter.as_callable()(message, context)
