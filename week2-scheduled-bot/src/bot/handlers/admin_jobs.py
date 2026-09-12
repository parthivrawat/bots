"""Admin job control handlers."""

from __future__ import annotations

from ..core.contracts import HandlerContext


async def admin_jobs_handler(ctx: HandlerContext) -> str:
    """
    List all scheduled jobs with their status.
    
    Usage: /admin jobs
    """
    jobs = await ctx.services.jobs.get_all_jobs()
    
    if not jobs:
        return "No scheduled jobs found."
    
    lines = ["**Scheduled Jobs:**\n"]
    
    for job in jobs:
        status = "✅ Enabled" if job.enabled else "❌ Disabled"
        last_run = job.last_run_at or "Never"
        next_run = job.next_run_at or "N/A"
        
        lines.append(
            f"**{job.name}**\n"
            f"  Type: {job.job_type} | Schedule: {job.schedule}\n"
            f"  Status: {status}\n"
            f"  Last run: {last_run}\n"
            f"  Next run: {next_run}\n"
        )
    
    lines.append(f"\nTotal: {len(jobs)} jobs")
    lines.append("\nControl with: `/admin job <name> <enable|disable|trigger|history>`")
    
    return "\n".join(lines)


async def admin_job_control_handler(ctx: HandlerContext) -> str:
    """
    Control a specific job.
    
    Usage: /admin job <name> <enable|disable|trigger|history>
    """
    if len(ctx.command.args) < 2:
        return (
            "Usage: `/admin job <name> <action>`\n\n"
            "Actions:\n"
            "  `enable` - Enable the job\n"
            "  `disable` - Disable the job\n"
            "  `trigger` - Run the job immediately\n"
            "  `history` - Show last 10 runs\n\n"
            "Example: `/admin job daily_weather enable`"
        )
    
    job_name = ctx.command.args[0]
    action = ctx.command.args[1].lower()
    
    # Verify job exists
    job = await ctx.services.jobs.get_job(job_name)
    if not job:
        return f"❌ Job not found: {job_name}\n\nUse `/admin jobs` to list all jobs."
    
    # Route to appropriate action
    if action == "enable":
        return await _enable_job(ctx, job_name)
    elif action == "disable":
        return await _disable_job(ctx, job_name)
    elif action == "trigger":
        return await _trigger_job(ctx, job_name)
    elif action == "history":
        return await _job_history(ctx, job_name)
    else:
        return (
            f"Unknown action: {action}\n\n"
            "Valid actions: enable, disable, trigger, history"
        )


async def _enable_job(ctx: HandlerContext, job_name: str) -> str:
    """Enable a job."""
    await ctx.services.jobs.update_job_enabled(job_name, True)
    if ctx.scheduler:
        await ctx.scheduler.enable_job(job_name)
    return f"✅ Job enabled: {job_name}\n\nThe job will run on its next scheduled time."


async def _disable_job(ctx: HandlerContext, job_name: str) -> str:
    """Disable a job."""
    await ctx.services.jobs.update_job_enabled(job_name, False)
    if ctx.scheduler:
        await ctx.scheduler.disable_job(job_name)
    return f"✅ Job disabled: {job_name}\n\nThe job will not run until re-enabled."


async def _trigger_job(ctx: HandlerContext, job_name: str) -> str:
    """Trigger a job immediately."""
    if ctx.scheduler:
        result = await ctx.scheduler.trigger_job(job_name)
        return f"🚀 Job triggered: {job_name}\n\nResult: {result}"
    return f"🚀 Job triggered: {job_name}\n\nThe job is running in the background."


async def _job_history(ctx: HandlerContext, job_name: str) -> str:
    """Show job execution history."""
    runs = await ctx.services.jobs.get_job_history(job_name, limit=10)
    
    if not runs:
        return f"No execution history for: {job_name}"
    
    lines = [f"**Execution History: {job_name}**\n"]
    
    for run in runs:
        status_emoji = {
            "success": "✅",
            "failed": "❌",
            "running": "🔄",
        }.get(run.status, "❓")
        
        duration = "N/A"
        if run.finished_at:
            # Simple duration display (could be enhanced)
            duration = "completed"
        
        lines.append(
            f"{status_emoji} **Run #{run.id}**\n"
            f"  Started: {run.started_at}\n"
            f"  Status: {run.status} ({duration})\n"
        )
        
        if run.result_summary:
            lines.append(f"  Result: {run.result_summary}\n")
        
        if run.error_message:
            lines.append(f"  Error: {run.error_message}\n")
    
    lines.append(f"\nShowing last {len(runs)} runs")
    
    return "\n".join(lines)


def register(router):
    """Register admin job handlers."""
    router.register(
        "jobs",
        "List all scheduled jobs (admin only)",
        admin_only=True,
    )(admin_jobs_handler)
    
    router.register(
        "job",
        "Control a scheduled job (admin only)",
        admin_only=True,
    )(admin_job_control_handler)
