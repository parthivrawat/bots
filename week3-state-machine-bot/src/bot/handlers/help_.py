from ..core.contracts import HandlerContext
from ..core.router import Router


def register(router: Router) -> None:
    @router.register("help", "List available commands")
    async def handle(ctx: HandlerContext) -> str:
        specs = router.visible_commands(ctx.user.is_admin)
        lines = [
            f"/{s.name} — {s.help_text}"
            for s in sorted(specs, key=lambda s: s.name)
            if s.help_text
        ]
        return "Available commands:\n" + "\n".join(lines)
