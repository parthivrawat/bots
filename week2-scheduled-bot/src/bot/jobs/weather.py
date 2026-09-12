"""Daily weather report job."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from apscheduler.triggers.cron import CronTrigger

from ..fetchers.weather_api import WeatherFetcher, format_weather_report

if TYPE_CHECKING:
    from ..app import App
    from .scheduler import JobScheduler

logger = logging.getLogger(__name__)


async def daily_weather_job(app: App) -> str:
    """
    Fetch weather and send to all users who enabled 'weather_report'.
    
    Runs daily at 9:00 AM UTC.
    """
    # Get users subscribed to weather reports
    users = await app.services.users.get_users_with_setting("weather_report", "on")
    
    if not users:
        return "No users subscribed to weather reports"
    
    sent_count = 0
    error_count = 0
    
    async with WeatherFetcher() as weather_api:
        for user in users:
            try:
                # Get user's city preference (default to London)
                city = await app.services.users.get_setting(
                    user.id, "city", default="London"
                )
                
                # Fetch weather
                weather = await weather_api.get_forecast(city)
                
                # Format message
                message = format_weather_report(weather)
                
                # Send to user (reuse Week 1 adapters)
                await app.send_to_user(user, message)
                
                sent_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send weather to user {user.id}: {e}")
                error_count += 1
    
    result = f"Sent to {sent_count} users"
    if error_count > 0:
        result += f", {error_count} errors"
    
    return result


async def register(scheduler: JobScheduler, app: App) -> None:
    """Register the daily weather job."""
    # Ensure job exists in database
    job_record = await app.services.jobs.get_job("daily_weather")
    if not job_record:
        await app.services.jobs.create_job(
            name="daily_weather",
            job_type="cron",
            schedule="0 9 * * *",  # 9:00 AM UTC daily
            enabled=True,
        )
    
    # Register with scheduler
    scheduler.register_job(
        name="daily_weather",
        func=daily_weather_job,
        trigger=CronTrigger(hour=9, minute=0, timezone="UTC"),
        enabled=job_record.enabled if job_record else True,
    )
