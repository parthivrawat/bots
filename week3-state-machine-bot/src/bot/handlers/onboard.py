"""Multi-step /onboard workflow to collect city and language."""

from __future__ import annotations

from ..core.contracts import HandlerContext
from ..core.errors import ValidationError
from ..core.router import Router
from ..core.state_machine import Transition, Workflow


def build_onboard_workflow() -> Workflow:
    async def _start(text: str, data: dict, ctx: HandlerContext) -> Transition:
        return Transition("city", data, "What city are you in?")

    async def _city(text: str, data: dict, ctx: HandlerContext) -> Transition:
        value = text.strip()
        if not value:
            return Transition("city", data, "City cannot be empty.")
        data["city"] = value
        return Transition("language", data, "Preferred language? (en, es, fr)")

    async def _language(text: str, data: dict, ctx: HandlerContext) -> Transition:
        value = text.strip().lower()
        if value not in ("en", "es", "fr"):
            return Transition("language", data, "Choose en, es, or fr.")
        data["language"] = value
        summary = f"City: {data['city']}\nLanguage: {data['language']}"
        return Transition("confirm", data, f"Confirm profile?\n{summary}\n\nReply 'yes' to save or /cancel to abort.")

    async def _confirm(text: str, data: dict, ctx: HandlerContext) -> Transition:
        if text.strip().lower() == "yes":
            try:
                await ctx.services.users.apply_setting(ctx.user, "locale", data["language"])
                await ctx.services.users.users.set_setting(ctx.user.id, "city", data["city"])
            except ValidationError as exc:
                return Transition("__done__", data, f"Could not save profile: {exc.user_message}")
            return Transition(
                "__done__", data,
                f"Profile updated.\nCity: {data['city']}\nLanguage: {data['language']}",
            )
        return Transition("confirm", data, "Reply 'yes' to confirm or /cancel to cancel.")

    return Workflow("onboard", "__start__", {
        "__start__": _start,
        "city": _city,
        "language": _language,
        "confirm": _confirm,
    })


def register(router: Router) -> None:
    if router.state_machine is not None:
        router.state_machine.register(build_onboard_workflow())

    @router.register("onboard", "Start the profile setup wizard")
    async def onboard_cmd(ctx: HandlerContext) -> str:
        if not ctx.services.state:
            return "State service is not available."
        return await ctx.services.state.start(ctx, "onboard")
