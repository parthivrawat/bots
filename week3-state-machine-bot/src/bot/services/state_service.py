"""State machine service: coordinates persistence and workflow transitions."""

from __future__ import annotations

import logging

from ..core.contracts import HandlerContext, User
from ..core.state_machine import StateMachine
from ..db.repositories.state_repo import StateRepository

logger = logging.getLogger(__name__)


class StateService:
    def __init__(self, repository: StateRepository, machine: StateMachine):
        self.repo = repository
        self.machine = machine

    async def get_active(self, user: User) -> dict | None:
        conv = await self.repo.get_active(user.id)
        if not conv:
            return None
        return {
            "id": conv.id,
            "workflow": conv.workflow,
            "state": conv.state,
            "data": conv.data,
        }

    async def start(self, ctx: HandlerContext, workflow: str) -> str:
        active = await self.repo.get_active(ctx.user.id)
        if active:
            return "You already have an active workflow. Send /cancel to stop."

        next_state, data, reply = await self.machine.start(workflow, ctx)
        if next_state == "__done__":
            return reply or "Workflow unavailable."

        await self.repo.start(ctx.user, workflow, next_state, data)
        return reply

    async def advance(self, ctx: HandlerContext, text: str) -> str:
        conv = await self.repo.get_active(ctx.user.id)
        if not conv:
            return "No active workflow. Send /report to start."

        result = await self.machine.advance(conv.workflow, conv.state, text, conv.data, ctx)

        if result.next_state == "__done__":
            await self.repo.set_status(conv.id, "completed")
        else:
            await self.repo.update(conv.id, result.next_state, result.data)

        return result.reply

    async def cancel(self, user: User) -> str:
        conv = await self.repo.get_active(user.id)
        if not conv:
            return "No active workflow to cancel."
        await self.repo.set_status(conv.id, "cancelled")
        return "Workflow cancelled."
