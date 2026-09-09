"""Domain errors. Handlers raise these; the router converts them into
user-facing OutgoingReply text and audit-log entries."""


class BotError(Exception):
    """Base error carrying a message safe to show the user."""

    user_message = "Something went wrong. Please try again."

    def __init__(self, user_message: str | None = None):
        super().__init__(user_message or self.user_message)
        if user_message:
            self.user_message = user_message


class UnknownCommand(BotError):
    user_message = "Unknown command. Try /help."


class PermissionDenied(BotError):
    user_message = "You don't have permission to use this command."


class Banned(PermissionDenied):
    user_message = "Your access to this bot has been revoked."


class RateLimited(BotError):
    user_message = "You're sending commands too fast. Slow down a moment."


class ValidationError(BotError):
    """Bad input the user can fix (unknown setting key, bad value, etc.)."""
    user_message = "Invalid input."
