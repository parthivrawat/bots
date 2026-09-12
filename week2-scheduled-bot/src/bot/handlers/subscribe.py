"""Subscription management handlers."""

from __future__ import annotations

from ..core.contracts import HandlerContext

# Valid subscription types
SUBSCRIPTIONS = {
    "weather": {
        "setting_key": "weather_report",
        "description": "Daily weather report at 9:00 AM UTC",
    },
}


async def subscribe_handler(ctx: HandlerContext) -> str:
    """
    Subscribe to a service.
    
    Usage: /subscribe weather
    """
    if not ctx.command.args:
        available = ", ".join(SUBSCRIPTIONS.keys())
        return f"Usage: /subscribe <service>\n\nAvailable: {available}"
    
    service = ctx.command.args[0].lower()
    
    if service not in SUBSCRIPTIONS:
        available = ", ".join(SUBSCRIPTIONS.keys())
        return f"Unknown service: {service}\n\nAvailable: {available}"
    
    sub = SUBSCRIPTIONS[service]
    
    # Set the subscription setting
    await ctx.services.users.users.set_setting(
        ctx.user.id, sub["setting_key"], "on"
    )
    
    return f"✅ Subscribed to **{service}**\n\n{sub['description']}\n\nUse `/unsubscribe {service}` to disable."


async def unsubscribe_handler(ctx: HandlerContext) -> str:
    """
    Unsubscribe from a service.
    
    Usage: /unsubscribe weather
    """
    if not ctx.command.args:
        available = ", ".join(SUBSCRIPTIONS.keys())
        return f"Usage: /unsubscribe <service>\n\nAvailable: {available}"
    
    service = ctx.command.args[0].lower()
    
    if service not in SUBSCRIPTIONS:
        available = ", ".join(SUBSCRIPTIONS.keys())
        return f"Unknown service: {service}\n\nAvailable: {available}"
    
    sub = SUBSCRIPTIONS[service]
    
    # Remove the subscription setting
    await ctx.services.users.users.set_setting(
        ctx.user.id, sub["setting_key"], "off"
    )
    
    return f"✅ Unsubscribed from **{service}**\n\nYou will no longer receive {service} updates."


def register(router):
    """Register subscription handlers."""
    router.register(
        "subscribe",
        "Subscribe to automated reports (e.g., /subscribe weather)",
    )(subscribe_handler)
    
    router.register(
        "unsubscribe",
        "Unsubscribe from automated reports",
    )(unsubscribe_handler)
