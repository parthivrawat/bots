from ..core.contracts import HandlerContext
from ..core.errors import ValidationError
from ..core.router import Router


def register(router: Router) -> None:
    @router.register("settings", "Show or update preferences: /settings key=value")
    async def handle(ctx: HandlerContext) -> str:
        if not ctx.command.kwargs:
            return await ctx.services.users.settings_text(ctx.user)
        if len(ctx.command.kwargs) > 1:
            raise ValidationError("Update one setting at a time: /settings key=value")
        (key, value), = ctx.command.kwargs.items()
        return await ctx.services.users.apply_setting(ctx.user, key, value)
