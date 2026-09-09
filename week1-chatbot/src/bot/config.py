"""Environment-driven configuration. Never hardcode secrets — load from .env."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass
class AppSettings:
    telegram_token: str | None = None
    discord_token: str | None = None
    db_path: str = "bot.db"
    admin_ids: set[str] = field(default_factory=set)   # "platform:id" entries
    rate_limit_capacity: int = 5
    rate_limit_window_s: float = 10.0

    @staticmethod
    def from_env(env_file: str = ".env") -> "AppSettings":
        load_dotenv(env_file)
        raw_admins = os.getenv("ADMIN_IDS", "")
        return AppSettings(
            telegram_token=os.getenv("TELEGRAM_TOKEN") or None,
            discord_token=os.getenv("DISCORD_TOKEN") or None,
            db_path=os.getenv("DB_PATH", "bot.db"),
            admin_ids={s.strip() for s in raw_admins.split(",") if s.strip()},
            rate_limit_capacity=int(os.getenv("RATE_LIMIT_CAPACITY", "5")),
            rate_limit_window_s=float(os.getenv("RATE_LIMIT_WINDOW_S", "10")),
        )
