"""User-facing business logic. Handlers call this, never the repo directly."""

from __future__ import annotations

from typing import Optional

from ..core.contracts import User
from ..core.errors import ValidationError
from ..db.repositories import UserRepository

# Settings users may change — anything else is rejected.
ALLOWED_SETTINGS = {
    "locale": {"en", "es", "fr", "de"},
    "timezone": None,     # any string accepted; validate format later if needed
    "notify": {"on", "off"},
}


class UserService:
    def __init__(self, users: UserRepository, admin_ids: set[str]):
        self.users = users
        self.admin_ids = admin_ids   # "platform:id" strings from config

    async def get_or_create(self, platform: str, platform_user_id: str,
                            username: Optional[str]) -> User:
        user = await self.users.get_or_create(platform, platform_user_id, username)
        # Bootstrap admins from config: env-listed ids get role=admin once.
        if f"{platform}:{platform_user_id}" in self.admin_ids and user.role == "user":
            await self.users.set_role(platform, platform_user_id, "admin")
            user = await self.users.get(platform, platform_user_id)
        return user

    async def profile_text(self, user: User) -> str:
        settings = await self.users.get_settings(user.id)
        lines = [
            "Profile",
            f"  Username: {user.username or '(none)'}",
            f"  Platform: {user.platform}",
            f"  Role:     {user.role}",
            f"  Locale:   {user.locale}",
            f"  Joined:   {user.created_at}",
        ]
        if settings:
            lines.append("  Settings: " + ", ".join(f"{k}={v}" for k, v in settings.items()))
        return "\n".join(lines)

    async def settings_text(self, user: User) -> str:
        settings = await self.users.get_settings(user.id)
        allowed = ", ".join(sorted(ALLOWED_SETTINGS))
        if not settings:
            return f"No custom settings. Available keys: {allowed}"
        body = "\n".join(f"  {k} = {v}" for k, v in settings.items())
        return f"Your settings:\n{body}\n(available keys: {allowed})"

    async def apply_setting(self, user: User, key: str, value: str) -> str:
        key = key.lower()
        if key not in ALLOWED_SETTINGS:
            raise ValidationError(
                f"Unknown setting '{key}'. Available: {', '.join(sorted(ALLOWED_SETTINGS))}"
            )
        choices = ALLOWED_SETTINGS[key]
        if choices is not None and value.lower() not in choices:
            raise ValidationError(
                f"Invalid value '{value}' for '{key}'. Choose: {', '.join(sorted(choices))}"
            )
        await self.users.set_setting(user.id, key, value)
        return f"Setting saved: {key} = {value}"

    async def get_setting(self, user_id: int, key: str, default: str | None = None) -> str | None:
        """Get a user setting."""
        return await self.users.get_setting(user_id, key, default)

    async def get_users_with_setting(self, key: str, value: str) -> list[User]:
        """Get all users who have a specific setting value."""
        return await self.users.get_users_with_setting(key, value)

    async def get_admins(self) -> list[User]:
        """Get all admin users."""
        return await self.users.get_admins()
