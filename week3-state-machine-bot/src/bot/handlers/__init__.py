"""Register all command handlers onto a Router. Import this once at startup."""

from ..core.router import Router


def register_all(router: Router) -> None:
    from . import admin, help_, onboard, profile, report, settings_, start  # noqa: F401
    for module in (start, help_, profile, settings_, admin, report, onboard):
        module.register(router)
