"""Application assembly: wire DB, repos, services, middleware, router.

This is the single composition root — adapters, tests, and the eval harness
all build the bot through build_app() so they share identical behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import AppSettings
from .core.middleware import RateLimiter, logging_middleware, make_auth_middleware, make_state_middleware
from .core.router import Router
from .core.state_machine import StateMachine
from .db.database import Database
from .db.repositories import AuditRepository, StateRepository, UserRepository
from .handlers import register_all
from .services import AdminService, StateService, UserService


@dataclass
class ServiceRegistry:
    users: UserService
    admin: AdminService
    audit: AuditRepository
    state: StateService


@dataclass
class App:
    settings: AppSettings
    db: Database
    services: ServiceRegistry
    router: Router
    adapters: list[Any] = field(default_factory=list)  # Set in main.py

    async def close(self) -> None:
        await self.db.close()


async def build_app(settings: AppSettings) -> App:
    db = Database(settings.db_path)
    await db.connect()

    user_repo = UserRepository(db)
    audit_repo = AuditRepository(db)
    state_repo = StateRepository(db)

    machine = StateMachine()
    state_service = StateService(state_repo, machine)

    services = ServiceRegistry(
        users=UserService(user_repo, settings.admin_ids),
        admin=AdminService(user_repo, audit_repo),
        audit=audit_repo,
        state=state_service,
    )

    router = Router(services=services, settings=settings)
    router.state_machine = machine
    router.middleware = [
        logging_middleware,
        make_auth_middleware(),
        make_state_middleware(),
        RateLimiter(
            capacity=settings.rate_limit_capacity,
            refill_seconds=settings.rate_limit_window_s,
        ),
    ]
    register_all(router)

    return App(settings=settings, db=db, services=services, router=router)
