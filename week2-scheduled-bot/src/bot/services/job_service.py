"""Service for managing scheduled jobs and alerts."""

from __future__ import annotations

from ..db.repositories.job_repo import JobRepository, PriceAlert, ScheduledJob, JobRun


class JobService:
    """Business logic for scheduled jobs."""

    def __init__(self, job_repo: JobRepository):
        self.repo = job_repo

    # -- Scheduled jobs --------------------------------------------------------

    async def get_all_jobs(self) -> list[ScheduledJob]:
        """Get all scheduled jobs."""
        return await self.repo.get_all_jobs()

    async def get_job(self, name: str) -> ScheduledJob | None:
        """Get a job by name."""
        return await self.repo.get_job(name)

    async def create_job(
        self, name: str, job_type: str, schedule: str, enabled: bool = True
    ) -> ScheduledJob:
        """Create a new scheduled job."""
        return await self.repo.create_job(name, job_type, schedule, enabled)

    async def update_job_enabled(self, name: str, enabled: bool) -> None:
        """Enable or disable a job."""
        await self.repo.update_job_enabled(name, enabled)

    async def update_job_run_times(
        self, name: str, last_run_at: str | None, next_run_at: str | None
    ) -> None:
        """Update job run times."""
        await self.repo.update_job_run_times(name, last_run_at, next_run_at)

    async def get_job_history(self, job_name: str, limit: int = 10) -> list[JobRun]:
        """Get recent runs for a job."""
        job = await self.repo.get_job(job_name)
        if not job:
            return []
        return await self.repo.get_job_runs(job.id, limit)

    # -- Job runs --------------------------------------------------------------

    async def create_job_run(self, job_id: int) -> int:
        """Create a new job run record."""
        return await self.repo.create_job_run(job_id)

    async def finish_job_run(
        self,
        run_id: int,
        status: str,
        result_summary: str | None = None,
        error_message: str | None = None,
        output_data: dict | None = None,
    ) -> None:
        """Mark a job run as finished."""
        await self.repo.finish_job_run(
            run_id, status, result_summary, error_message, output_data
        )

    async def log_delivery(
        self,
        run_id: int,
        platform: str,
        platform_user_id: str,
        message_id: str | None = None,
    ) -> None:
        """Log a job delivery."""
        await self.repo.log_delivery(run_id, platform, platform_user_id, message_id)

    # -- Price alerts ----------------------------------------------------------

    async def create_price_alert(
        self, user_id: int, symbol: str, condition: str, threshold: float
    ) -> int:
        """Create a price alert."""
        # Validate condition
        if condition not in ("above", "below"):
            raise ValueError(f"Invalid condition: {condition}")
        
        # Validate threshold
        if threshold <= 0:
            raise ValueError("Threshold must be positive")
        
        return await self.repo.create_price_alert(user_id, symbol, condition, threshold)

    async def get_user_alerts(self, user_id: int) -> list[PriceAlert]:
        """Get all alerts for a user."""
        return await self.repo.get_user_alerts(user_id)

    async def get_active_alerts(self) -> list[PriceAlert]:
        """Get all active (not triggered) alerts."""
        return await self.repo.get_active_alerts()

    async def mark_alert_triggered(self, alert_id: int) -> None:
        """Mark an alert as triggered."""
        await self.repo.mark_alert_triggered(alert_id)

    async def delete_alert(self, alert_id: int, user_id: int) -> bool:
        """Delete an alert (only if owned by user)."""
        return await self.repo.delete_alert(alert_id, user_id)
