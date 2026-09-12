from ..core.contracts import HandlerContext
from ..core.router import Router

WELCOME = (
    "Welcome! I'm your assistant bot.\n"
    "Your account is ready. Try /help to see what I can do."
)


def register(router: Router) -> None:
    @router.register("start", "Register and see the welcome message")
    async def handle(ctx: HandlerContext) -> str:
        return WELCOME
