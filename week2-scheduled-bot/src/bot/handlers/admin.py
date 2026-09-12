from ..core.contracts import Command, HandlerContext
from ..core.errors import ValidationError
from ..core.router import Router
from . import admin_jobs

USAGE = "Usage: /admin stats | /admin ban <platform>:<id> | /admin unban <platform>:<id> | /admin broadcast <msg>"


def register(router: Router) -> None:
    @router.register("admin", "Admin operations", admin_only=True)
    async def handle(ctx: HandlerContext) -> str:
        if not ctx.command.args:
            raise ValidationError(USAGE)
        sub, *rest = ctx.command.args
        svc = ctx.services.admin
        if sub == "stats":
            return await svc.stats_text()
        if sub == "ban":
            if not rest:
                raise ValidationError(USAGE)
            return await svc.ban(rest[0])
        if sub == "unban":
            if not rest:
                raise ValidationError(USAGE)
            return await svc.unban(rest[0])
        if sub == "broadcast":
            return await svc.broadcast(" ".join(rest))
        if sub == "jobs":
            ctx.command = Command(name="jobs", args=rest, kwargs=ctx.command.kwargs)
            return await admin_jobs.admin_jobs_handler(ctx)
        if sub == "job":
            ctx.command = Command(name="job", args=rest, kwargs=ctx.command.kwargs)
            return await admin_jobs.admin_job_control_handler(ctx)
        raise ValidationError(USAGE)
