"""Application assembly: wire DB, repos, services, middleware, router.

This is the single composition root — adapters, tests, and the eval harness
all build the bot through build_app() so they share identical behavior.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .config import AppSettings
from .core.contracts import OutgoingReply, User
from .core.middleware import RateLimiter, logging_middleware, make_auth_middleware
from .core.router import Router
from .db.database import Database
from .db.repositories import AuditRepository, UserRepository
from .db.repositories.job_repo import JobRepository
from .handlers import register_all
from .services import AdminService, UserService
from .services.job_service import JobService


@dataclass
class ServiceRegistry:
    users: UserService
    admin: AdminService
    audit: AuditRepository
    jobs: JobService


@dataclass
class App:
    settings: AppSettings
    db: Database
    services: ServiceRegistry
    router: Router
    scheduler: "JobScheduler | None" = None  # Set after build_app()
    adapters: list[Any] = field(default_factory=list)  # Set in main.py

    async def close(self) -> None:
        if self.scheduler:
            await self.scheduler.stop()
        await self.db.close()

    async def send_to_user(self, user: User, message: str) -> None:
        """
        Send a message to a user on their platform.

        Scheduled jobs use this to deliver proactive messages.
        The correct platform adapter is chosen by matching user.platform.
        """
        logger = logging.getLogger(__name__)
        for adapter in self.adapters:
            platform = getattr(adapter, "platform", None)
            if platform == user.platform:
                if hasattr(adapter, "send"):
                    logger.info("Delivering %s message to %s", user.platform, user.platform_user_id)
                    return await adapter.send(user, message)
                raise RuntimeError(f"Adapter for {user.platform} has no send() method")
        raise RuntimeError(f"No adapter configured for {user.platform}; message not delivered")


async def build_app(settings: AppSettings) -> App:
    db = Database(settings.db_path)
    await db.connect()

    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)
    job_repo = JobRepository(db)
    
    services = ServiceRegistry(
        users=UserService(user_repo, settings.admin_ids),
        admin=AdminService(user_repo, audit_repo),
        audit=audit_repo,
        jobs=JobService(job_repo),
    )

    router = Router(services=services, settings=settings)
    router.middleware = [
        logging_middleware,
        make_auth_middleware(),
        RateLimiter(
            capacity=settings.rate_limit_capacity,
            refill_seconds=settings.rate_limit_window_s,
        ),
    ]
    register_all(router)

    app = App(settings=settings, db=db, services=services, router=router)
    
    # Initialize scheduler (Week 2)
    from .jobs import JobScheduler
    scheduler = JobScheduler(app)
    await scheduler._register_all_jobs()
    app.scheduler = scheduler
    app.router.scheduler = scheduler
    
    return app
