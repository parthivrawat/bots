import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bot.app import build_app  # noqa: E402
from bot.config import AppSettings  # noqa: E402
from bot.core.contracts import IncomingMessage  # noqa: E402


def run(coro):
    """Each test gets a fresh loop AND a fresh app built inside it —
    asyncio primitives (locks) bind to the loop that first uses them."""
    return asyncio.run(coro)


@pytest.fixture
def make_app(tmp_path):
    def factory(**overrides):
        settings = AppSettings(
            db_path=str(tmp_path / "test.db"),
            admin_ids=overrides.pop("admin_ids", {"eval:admin-1"}),
            **overrides,
        )

        async def build():
            return await build_app(settings)

        return asyncio.run(build())
    return factory


def msg(text: str, uid: str = "u1", platform: str = "eval", username: str = "tester"):
    return IncomingMessage(
        platform=platform, platform_user_id=uid, username=username, text=text
    )
