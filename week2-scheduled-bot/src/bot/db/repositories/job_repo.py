"""Repository for scheduled jobs and job runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..database import Database


@dataclass
class ScheduledJob:
    id: int
    name: str
    job_type: str
    schedule: str
    enabled: bool
    last_run_at: str | None
    next_run_at: str | None
    created_at: str
    updated_at: str


@dataclass
class JobRun:
    id: int
    job_id: int
    started_at: str
    finished_at: str | None
    status: str
    result_summary: str | None
    error_message: str | None
    output_data: dict | None


@dataclass
class PriceAlert:
    id: int
    user_id: int
    symbol: str
    condition: str
    threshold: float
    triggered: bool
    triggered_at: str | None
    created_at: str


class JobRepository:
    def __init__(self, db: Database):
        self.db = db

    # -- Scheduled jobs --------------------------------------------------------

    async def get_all_jobs(self) -> list[ScheduledJob]:
        """Get all scheduled jobs."""
        async with self.db.conn.execute(
            "SELECT * FROM scheduled_jobs ORDER BY name"
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_job(row) for row in rows]

    async def get_job(self, name: str) -> ScheduledJob | None:
        """Get a job by name."""
        async with self.db.conn.execute(
            "SELECT * FROM scheduled_jobs WHERE name = ?", (name,)
        ) as cursor:
            row = await cursor.fetchone()
            return self._row_to_job(row) if row else None

    async def create_job(
        self, name: str, job_type: str, schedule: str, enabled: bool = True
    ) -> ScheduledJob:
        """Create a new scheduled job."""
        async with self.db.conn.execute(
            """
            INSERT INTO scheduled_jobs (name, job_type, schedule, enabled)
            VALUES (?, ?, ?, ?)
            """,
            (name, job_type, schedule, int(enabled)),
        ) as cursor:
            job_id = cursor.lastrowid
        await self.db.conn.commit()
        job = await self.get_job(name)
        assert job is not None
        return job

    async def update_job_enabled(self, name: str, enabled: bool) -> None:
        """Enable or disable a job."""
        await self.db.conn.execute(
            "UPDATE scheduled_jobs SET enabled = ?, updated_at = datetime('now') WHERE name = ?",
            (int(enabled), name),
        )
        await self.db.conn.commit()

    async def update_job_run_times(
        self, name: str, last_run_at: str | None, next_run_at: str | None
    ) -> None:
        """Update job run times."""
        await self.db.conn.execute(
            """
            UPDATE scheduled_jobs
            SET last_run_at = ?, next_run_at = ?, updated_at = datetime('now')
            WHERE name = ?
            """,
            (last_run_at, next_run_at, name),
        )
        await self.db.conn.commit()

    # -- Job runs --------------------------------------------------------------

    async def create_job_run(self, job_id: int) -> int:
        """Create a new job run record (status='running')."""
        async with self.db.conn.execute(
            "INSERT INTO job_runs (job_id, status) VALUES (?, 'running')",
            (job_id,),
        ) as cursor:
            run_id = cursor.lastrowid
        await self.db.conn.commit()
        return run_id

    async def finish_job_run(
        self,
        run_id: int,
        status: str,
        result_summary: str | None = None,
        error_message: str | None = None,
        output_data: dict | None = None,
    ) -> None:
        """Mark a job run as finished."""
        await self.db.conn.execute(
            """
            UPDATE job_runs
            SET finished_at = datetime('now'), status = ?, result_summary = ?,
                error_message = ?, output_data = ?
            WHERE id = ?
            """,
            (
                status,
                result_summary,
                error_message,
                json.dumps(output_data) if output_data else None,
                run_id,
            ),
        )
        await self.db.conn.commit()

    async def get_job_runs(self, job_id: int, limit: int = 10) -> list[JobRun]:
        """Get recent runs for a job."""
        async with self.db.conn.execute(
            """
            SELECT * FROM job_runs
            WHERE job_id = ?
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (job_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_job_run(row) for row in rows]

    async def log_delivery(
        self,
        run_id: int,
        platform: str,
        platform_user_id: str,
        message_id: str | None = None,
    ) -> None:
        """Log a job delivery."""
        await self.db.conn.execute(
            """
            INSERT INTO job_deliveries (job_run_id, platform, platform_user_id, message_id)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, platform, platform_user_id, message_id),
        )
        await self.db.conn.commit()

    # -- Price alerts ----------------------------------------------------------

    async def create_price_alert(
        self, user_id: int, symbol: str, condition: str, threshold: float
    ) -> int:
        """Create a price alert."""
        async with self.db.conn.execute(
            """
            INSERT INTO price_alerts (user_id, symbol, condition, threshold)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, symbol.upper(), condition, threshold),
        ) as cursor:
            alert_id = cursor.lastrowid
        await self.db.conn.commit()
        return alert_id

    async def get_user_alerts(self, user_id: int) -> list[PriceAlert]:
        """Get all alerts for a user."""
        async with self.db.conn.execute(
            "SELECT * FROM price_alerts WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_alert(row) for row in rows]

    async def get_active_alerts(self) -> list[PriceAlert]:
        """Get all active (not triggered) alerts."""
        async with self.db.conn.execute(
            "SELECT * FROM price_alerts WHERE triggered = 0"
        ) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_alert(row) for row in rows]

    async def mark_alert_triggered(self, alert_id: int) -> None:
        """Mark an alert as triggered."""
        await self.db.conn.execute(
            """
            UPDATE price_alerts
            SET triggered = 1, triggered_at = datetime('now')
            WHERE id = ?
            """,
            (alert_id,),
        )
        await self.db.conn.commit()

    async def delete_alert(self, alert_id: int, user_id: int) -> bool:
        """Delete an alert (only if owned by user)."""
        async with self.db.conn.execute(
            "DELETE FROM price_alerts WHERE id = ? AND user_id = ?",
            (alert_id, user_id),
        ) as cursor:
            deleted = cursor.rowcount > 0
        await self.db.conn.commit()
        return deleted

    # -- Helpers ---------------------------------------------------------------

    @staticmethod
    def _row_to_job(row) -> ScheduledJob:
        return ScheduledJob(
            id=row[0],
            name=row[1],
            job_type=row[2],
            schedule=row[3],
            enabled=bool(row[4]),
            last_run_at=row[5],
            next_run_at=row[6],
            created_at=row[7],
            updated_at=row[8],
        )

    @staticmethod
    def _row_to_job_run(row) -> JobRun:
        return JobRun(
            id=row[0],
            job_id=row[1],
            started_at=row[2],
            finished_at=row[3],
            status=row[4],
            result_summary=row[5],
            error_message=row[6],
            output_data=json.loads(row[7]) if row[7] else None,
        )

    @staticmethod
    def _row_to_alert(row) -> PriceAlert:
        return PriceAlert(
            id=row[0],
            user_id=row[1],
            symbol=row[2],
            condition=row[3],
            threshold=row[4],
            triggered=bool(row[5]),
            triggered_at=row[6],
            created_at=row[7],
        )
