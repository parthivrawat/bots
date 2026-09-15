"""Multi-step /report workflow using the state machine engine."""

from __future__ import annotations

from ..core.contracts import HandlerContext
from ..core.router import Router
from ..core.state_machine import Transition, Workflow


def build_report_workflow() -> Workflow:
    async def _start(text: str, data: dict, ctx: HandlerContext) -> Transition:
        return Transition("category", data, "What category? (bug, feature, question)")

    async def _category(text: str, data: dict, ctx: HandlerContext) -> Transition:
        value = text.strip().lower()
        if value not in ("bug", "feature", "question"):
            return Transition("category", data, "Please choose bug, feature, or question.")
        data["category"] = value
        return Transition("description", data, "Please describe the issue.")

    async def _description(text: str, data: dict, ctx: HandlerContext) -> Transition:
        value = text.strip()
        if not value:
            return Transition("description", data, "Description cannot be empty.")
        data["description"] = value
        summary = f"Category: {data['category']}\nDescription: {data['description']}"
        return Transition("confirm", data, f"Confirm report?\n{summary}\n\nReply 'yes' to submit or /cancel to abort.")

    async def _confirm(text: str, data: dict, ctx: HandlerContext) -> Transition:
        if text.strip().lower() == "yes":
            summary = f"Report submitted.\nCategory: {data['category']}\nDescription: {data['description']}"
            return Transition("__done__", data, summary)
        return Transition("confirm", data, "Reply 'yes' to confirm or /cancel to cancel.")

    return Workflow("report", "__start__", {
        "__start__": _start,
        "category": _category,
        "description": _description,
        "confirm": _confirm,
    })


def register(router: Router) -> None:
    if router.state_machine is not None:
        router.state_machine.register(build_report_workflow())

    @router.register("report", "Start a bug/feature/question report")
    async def report_cmd(ctx: HandlerContext) -> str:
        if not ctx.services.state:
            return "State service is not available."
        return await ctx.services.state.start(ctx, "report")

    @router.register("__state__", "", admin_only=False)
    async def state_cmd(ctx: HandlerContext) -> str:
        if not ctx.services.state:
            return "State service is not available."
        return await ctx.services.state.advance(ctx, ctx.message.text)

    @router.register("cancel", "Cancel the active workflow")
    async def cancel_cmd(ctx: HandlerContext) -> str:
        if not ctx.services.state:
            return "State service is not available."
        return await ctx.services.state.cancel(ctx.user)
