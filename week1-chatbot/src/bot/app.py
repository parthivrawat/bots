"""Application assembly: wire DB, repos, services, middleware, router.

This is the single composition root — adapters, tests, and the eval harness
all build the bot through build_app() so they share identical behavior.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import AppSettings
from .core.middleware import RateLimiter, logging_middleware, make_auth_middleware
from .core.router import Router
from .db.database import Database
from .db.repositories import AuditRepository, UserRepository
from .handlers import register_all
from .services import AdminService, UserService


@dataclass
class ServiceRegistry:
    users: UserService
    admin: AdminService
    audit: AuditRepository


@dataclass
class App:
    settings: AppSettings
    db: Database
    services: ServiceRegistry
    router: Router

    async def close(self) -> None:
        await self.db.close()


async def build_app(settings: AppSettings) -> App:
    db = Database(settings.db_path)
    await db.connect()

    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)
    services = ServiceRegistry(
        users=UserService(user_repo, settings.admin_ids),
        admin=AdminService(user_repo, audit_repo),
        audit=audit_repo,
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

    return App(settings=settings, db=db, services=services, router=router)
