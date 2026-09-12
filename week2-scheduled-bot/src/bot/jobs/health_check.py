"""System health check job."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from apscheduler.triggers.interval import IntervalTrigger

if TYPE_CHECKING:
    from ..app import App
    from .scheduler import JobScheduler

logger = logging.getLogger(__name__)


async def health_check_job(app: App) -> str:
    """
    Check system health and alert admins if issues detected.
    
    Runs every 5 minutes.
    """
    checks = {}
    
    # Check database
    try:
        async with app.db.conn.execute("SELECT 1") as cursor:
            await cursor.fetchone()
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = False
    
    # Check weather API (optional - could be slow)
    # Skipping for now to avoid rate limits
    
    # Check crypto API (optional - could be slow)
    # Skipping for now to avoid rate limits
    
    # Identify failures
    failures = [name for name, healthy in checks.items() if not healthy]
    
    if failures:
        # Alert admins
        admins = await app.services.users.get_admins()
        message = f"⚠️ **Health Check Failed**\n\nUnhealthy services: {', '.join(failures)}"

        for admin in admins:
            try:
                await app.send_to_user(admin, message)
            except Exception as e:
                logger.error(f"Failed to alert admin {admin.id}: {e}")

        raise HealthCheckError(f"UNHEALTHY: {', '.join(failures)}")

    return "All systems healthy"


class HealthCheckError(Exception):
    """Raised when a health check finds unhealthy services."""


async def register(scheduler: JobScheduler, app: App) -> None:
    """Register the health check job."""
    # Ensure job exists in database
    job_record = await app.services.jobs.get_job("health_check")
    if not job_record:
        await app.services.jobs.create_job(
            name="health_check",
            job_type="interval",
            schedule="300",  # 5 minutes in seconds
            enabled=True,
        )
    
    # Register with scheduler
    scheduler.register_job(
        name="health_check",
        func=health_check_job,
        trigger=IntervalTrigger(minutes=5, timezone="UTC"),
        enabled=job_record.enabled if job_record else True,
    )
