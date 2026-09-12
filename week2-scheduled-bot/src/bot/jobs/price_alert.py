"""Crypto price alert job."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from apscheduler.triggers.interval import IntervalTrigger

from ..fetchers.crypto_api import CryptoAPIError, CryptoFetcher, format_price_alert

if TYPE_CHECKING:
    from ..app import App
    from .scheduler import JobScheduler

logger = logging.getLogger(__name__)


async def price_alert_job(app: App) -> str:
    """
    Check crypto prices and alert users if thresholds crossed.
    
    Runs every 15 minutes.
    """
    # Get all active (not triggered) alerts
    alerts = await app.services.jobs.get_active_alerts()
    
    if not alerts:
        return "No active alerts"
    
    triggered_count = 0
    error_count = 0
    skipped_count = 0
    api_failed = False

    async with CryptoFetcher() as crypto_api:
        for alert in alerts:
            if api_failed:
                skipped_count += 1
                continue

            try:
                current_price = await crypto_api.get_price(alert.symbol)

                should_trigger = False
                if alert.condition == "above" and current_price > alert.threshold:
                    should_trigger = True
                elif alert.condition == "below" and current_price < alert.threshold:
                    should_trigger = True

                if should_trigger:
                    user = await app.services.users.get(alert.user_id)
                    if not user:
                        logger.error(f"User not found for alert {alert.id}")
                        continue

                    message = format_price_alert(
                        alert.symbol, current_price, alert.condition, alert.threshold
                    )
                    await app.send_to_user(user, message)
                    await app.services.jobs.mark_alert_triggered(alert.id)

                    triggered_count += 1
                    logger.info(
                        f"Triggered alert {alert.id}: {alert.symbol} "
                        f"{alert.condition} ${alert.threshold}"
                    )

            except CryptoAPIError as e:
                logger.error(f"CoinGecko API failed for {alert.symbol}: {e}")
                error_count += 1
                api_failed = True
            except Exception as e:
                logger.error(f"Failed to process alert {alert.id}: {e}")
                error_count += 1

    result = f"Checked {len(alerts)} alerts, triggered {triggered_count}"
    if skipped_count > 0:
        result += f", {skipped_count} skipped after API failure"
    if error_count > 0:
        result += f", {error_count} errors"

    return result


async def register(scheduler: JobScheduler, app: App) -> None:
    """Register the price alert job."""
    # Ensure job exists in database
    job_record = await app.services.jobs.get_job("price_alerts")
    if not job_record:
        await app.services.jobs.create_job(
            name="price_alerts",
            job_type="interval",
            schedule="900",  # 15 minutes in seconds
            enabled=True,
        )
    
    # Register with scheduler
    scheduler.register_job(
        name="price_alerts",
        func=price_alert_job,
        trigger=IntervalTrigger(minutes=15, timezone="UTC"),
        enabled=job_record.enabled if job_record else True,
    )
