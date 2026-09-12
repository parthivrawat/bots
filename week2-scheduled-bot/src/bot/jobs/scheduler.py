"""APScheduler-based job scheduler with persistence."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

if TYPE_CHECKING:
    from ..app import App

logger = logging.getLogger(__name__)

JobFunc = Callable[[Any], Awaitable[str]]


class JobScheduler:
    """
    Manages scheduled jobs using APScheduler.
    
    Jobs are registered programmatically and persisted to the database.
    On startup, jobs are re-registered from the database.
    """

    def __init__(self, app: App):
        self.app = app
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self._jobs: dict[str, JobFunc] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def start(self) -> None:
        """Start the scheduler and register all jobs."""
        logger.info("Starting job scheduler")
        
        # Register all job definitions
        await self._register_all_jobs()
        
        # Start APScheduler
        self.scheduler.start()
        logger.info(f"Scheduler started with {len(self._jobs)} jobs")

    async def stop(self) -> None:
        """Stop the scheduler gracefully."""
        logger.info("Stopping job scheduler")
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")

    def register_job(
        self,
        name: str,
        func: JobFunc,
        trigger: CronTrigger | IntervalTrigger,
        enabled: bool = True,
    ) -> None:
        """
        Register a job with the scheduler.
        
        Args:
            name: Unique job name
            func: Async function to execute
            trigger: APScheduler trigger (cron or interval)
            enabled: Whether job is enabled
        """
        self._jobs[name] = func
        
        if enabled:
            self.scheduler.add_job(
                self._execute_job,
                trigger,
                args=[name],
                id=name,
                name=name,
                replace_existing=True,
                max_instances=1,  # Prevent overlapping runs
            )
            logger.info(f"Registered job: {name}")

    async def trigger_job(self, name: str) -> str:
        """Manually trigger a job (for testing or admin commands)."""
        if name not in self._jobs:
            raise ValueError(f"Unknown job: {name}")
        
        logger.info(f"Manually triggering job: {name}")
        return await self._execute_job(name)

    async def enable_job(self, name: str) -> None:
        """Enable a job."""
        if name not in self._jobs:
            raise ValueError(f"Unknown job: {name}")
        
        await self.app.services.jobs.update_job_enabled(name, True)
        
        # Re-register with APScheduler
        job_record = await self.app.services.jobs.get_job(name)
        if job_record:
            trigger = self._parse_trigger(job_record.job_type, job_record.schedule)
            self.scheduler.add_job(
                self._execute_job,
                trigger,
                args=[name],
                id=name,
                name=name,
                replace_existing=True,
                max_instances=1,
            )
        logger.info(f"Enabled job: {name}")

    async def disable_job(self, name: str) -> None:
        """Disable a job."""
        if name not in self._jobs:
            raise ValueError(f"Unknown job: {name}")
        
        await self.app.services.jobs.update_job_enabled(name, False)
        
        # Remove from APScheduler
        if self.scheduler.get_job(name):
            self.scheduler.remove_job(name)
        logger.info(f"Disabled job: {name}")

    async def _execute_job(self, name: str) -> str:
        """
        Execute a job and log the result.
        
        Returns:
            Result summary string
        """
        func = self._jobs.get(name)
        if not func:
            logger.error(f"Job function not found: {name}")
            return "ERROR: Job not found"

        # Get job record
        job_record = await self.app.services.jobs.get_job(name)
        if not job_record:
            logger.error(f"Job record not found in DB: {name}")
            return "ERROR: Job record not found"

        lock = self._locks.setdefault(name, asyncio.Lock())
        async with lock:
            # Create job run record
            run_id = await self.app.services.jobs.create_job_run(job_record.id)

            try:
                logger.info(f"Executing job: {name} (run_id={run_id})")
                result = await func(self.app)

                # Mark as success
                await self.app.services.jobs.finish_job_run(
                    run_id, status="success", result_summary=result
                )

                logger.info(f"Job completed: {name} - {result}")
                return result

            except Exception as e:
                logger.exception(f"Job failed: {name}")

                # Mark as failed
                await self.app.services.jobs.finish_job_run(
                    run_id,
                    status="failed",
                    error_message=str(e),
                )

                return f"ERROR: {str(e)}"

            finally:
                # Update last_run_at regardless of success or failure
                now = datetime.now(timezone.utc).isoformat()
                next_run = self.scheduler.get_job(name)
                next_run_time = None
                if next_run is not None:
                    nrt = getattr(next_run, "next_run_time", None)
                    if nrt is not None:
                        next_run_time = nrt.isoformat()
                await self.app.services.jobs.update_job_run_times(
                    name, last_run_at=now, next_run_at=next_run_time
                )

    async def _register_all_jobs(self) -> None:
        """Register all job definitions from job modules."""
        # Import job modules
        from . import weather, price_alert, health_check
        
        # Register each job
        for module in [weather, price_alert, health_check]:
            await module.register(self, self.app)

    @staticmethod
    def _parse_trigger(job_type: str, schedule: str) -> CronTrigger | IntervalTrigger:
        """Parse job schedule into APScheduler trigger."""
        if job_type == "cron":
            # Parse cron expression (e.g., "0 9 * * *")
            parts = schedule.split()
            if len(parts) == 5:
                minute, hour, day, month, day_of_week = parts
                return CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                    timezone="UTC",
                )
            else:
                raise ValueError(f"Invalid cron expression: {schedule}")
        
        elif job_type == "interval":
            # Parse interval in seconds (e.g., "900" for 15 minutes)
            seconds = int(schedule)
            return IntervalTrigger(seconds=seconds, timezone="UTC")
        
        else:
            raise ValueError(f"Unknown job type: {job_type}")
