from ..core.contracts import HandlerContext
from ..core.router import Router


def register(router: Router) -> None:
    @router.register("profile", "Show your profile and preferences")
    async def handle(ctx: HandlerContext) -> str:
        return await ctx.services.users.profile_text(ctx.user)
