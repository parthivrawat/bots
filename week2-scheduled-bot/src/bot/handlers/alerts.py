"""Price alert handlers."""

from __future__ import annotations

from ..core.contracts import HandlerContext
from ..core.errors import ValidationError


async def alert_handler(ctx: HandlerContext) -> str:
    """
    Create a price alert.
    
    Usage: /alert BTC above 50000
           /alert ETH below 3000
    """
    if len(ctx.command.args) < 3:
        return (
            "Usage: `/alert <SYMBOL> <above|below> <PRICE>`\n\n"
            "Examples:\n"
            "  `/alert BTC above 50000`\n"
            "  `/alert ETH below 3000`\n\n"
            "Supported symbols: BTC, ETH, USDT, BNB, SOL, XRP, ADA, DOGE"
        )
    
    symbol = ctx.command.args[0].upper()
    condition = ctx.command.args[1].lower()
    
    try:
        threshold = float(ctx.command.args[2])
    except ValueError:
        return f"Invalid price: {ctx.command.args[2]}\n\nPrice must be a number."
    
    # Validate condition
    if condition not in ("above", "below"):
        return f"Invalid condition: {condition}\n\nUse 'above' or 'below'."
    
    # Validate symbol (will raise if unknown)
    from ..fetchers.crypto_api import CryptoFetcher
    if symbol not in CryptoFetcher.SYMBOL_MAP:
        supported = ", ".join(sorted(CryptoFetcher.SYMBOL_MAP.keys()))
        return f"Unknown symbol: {symbol}\n\nSupported: {supported}"
    
    # Create alert
    try:
        alert_id = await ctx.services.jobs.create_price_alert(
            ctx.user.id, symbol, condition, threshold
        )
        
        emoji = "🚀" if condition == "above" else "📉"
        return (
            f"{emoji} **Price alert created!**\n\n"
            f"Symbol: {symbol}\n"
            f"Condition: {condition} ${threshold:,.2f}\n"
            f"Alert ID: {alert_id}\n\n"
            f"You'll be notified when the price crosses this threshold.\n"
            f"Use `/alerts` to see all your alerts."
        )
    except (ValidationError, ValueError) as e:
        return str(e)


async def alerts_list_handler(ctx: HandlerContext) -> str:
    """
    List all price alerts for the current user.
    
    Usage: /alerts
    """
    alerts = await ctx.services.jobs.get_user_alerts(ctx.user.id)
    
    if not alerts:
        return (
            "You have no price alerts.\n\n"
            "Create one with: `/alert BTC above 50000`"
        )
    
    lines = ["**Your Price Alerts:**\n"]
    
    for alert in alerts:
        status = "✅ Active" if not alert.triggered else f"✓ Triggered on {alert.triggered_at}"
        emoji = "🚀" if alert.condition == "above" else "📉"
        
        lines.append(
            f"{emoji} **{alert.symbol}** {alert.condition} ${alert.threshold:,.2f}\n"
            f"   ID: {alert.id} | {status}"
        )
    
    lines.append(f"\nTotal: {len(alerts)} alerts")
    lines.append("\nCancel with: `/alert cancel <ID>`")
    
    return "\n".join(lines)


async def alert_cancel_handler(ctx: HandlerContext) -> str:
    """
    Cancel a price alert.
    
    Usage: /alert cancel <ID>
    """
    # This is called when command is "/alert cancel 123"
    # ctx.command.args = ["cancel", "123"]
    
    if len(ctx.command.args) < 2:
        return "Usage: `/alert cancel <ID>`\n\nGet alert IDs with `/alerts`"
    
    try:
        alert_id = int(ctx.command.args[1])
    except ValueError:
        return f"Invalid alert ID: {ctx.command.args[1]}\n\nID must be a number."
    
    # Delete alert (only if owned by user)
    deleted = await ctx.services.jobs.delete_alert(alert_id, ctx.user.id)
    
    if deleted:
        return f"✅ Alert {alert_id} cancelled."
    else:
        return f"❌ Alert {alert_id} not found or not owned by you."


async def alert_router(ctx: HandlerContext) -> str:
    """
    Route /alert commands to appropriate handler.
    
    /alert BTC above 50000  -> create alert
    /alert cancel 123       -> cancel alert
    /alert                  -> show usage
    """
    if not ctx.command.args:
        return (
            "**Price Alerts**\n\n"
            "Create: `/alert <SYMBOL> <above|below> <PRICE>`\n"
            "List: `/alerts`\n"
            "Cancel: `/alert cancel <ID>`\n\n"
            "Example: `/alert BTC above 50000`"
        )
    
    # Check if first arg is "cancel"
    if ctx.command.args[0].lower() == "cancel":
        return await alert_cancel_handler(ctx)
    else:
        return await alert_handler(ctx)


def register(router):
    """Register alert handlers."""
    router.register(
        "alert",
        "Create or manage price alerts (e.g., /alert BTC above 50000)",
    )(alert_router)
    
    router.register(
        "alerts",
        "List your price alerts",
    )(alerts_list_handler)
