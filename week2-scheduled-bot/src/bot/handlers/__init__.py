"""Register all command handlers onto a Router. Import this once at startup."""

from ..core.router import Router


def register_all(router: Router) -> None:
    from . import admin, alerts, help_, profile, settings_, start, subscribe  # noqa: F401
    for module in (start, help_, profile, settings_, admin, subscribe, alerts):
        module.register(router)
