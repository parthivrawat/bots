"""State middleware: capture free-form replies while a user is in a workflow.

When a user has an active conversation and sends a non-command message, the
router is redirected to the synthetic __state__ command so the state machine can
process the input.
"""

from __future__ import annotations

from ..contracts import Command, HandlerContext


def make_state_middleware():
    async def state_mw(ctx: HandlerContext) -> None:
        if ctx.user is None:
            return
        services = ctx.services
        if not getattr(services, "state", None):
            return

        active = await services.state.get_active(ctx.user)
        if not active:
            return

        text = ctx.message.text.strip()
        # Let explicit commands through (e.g. /cancel, /help); free-form text
        # belongs to the active workflow.
        if text.startswith("/") or text.startswith("!"):
            return

        ctx.command = Command(name="__state__", args=[], kwargs={})

    return state_mw
