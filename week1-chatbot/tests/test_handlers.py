"""Core-level tests: drive dispatch() directly — no platform code involved."""

import asyncio

from conftest import msg, run


def test_start_registers_and_is_idempotent(make_app):
    app = make_app()

    async def scenario():
        r1 = await app.router.dispatch(msg("/start"))
        r2 = await app.router.dispatch(msg("/start"))
        assert "Welcome" in r1.text and "Welcome" in r2.text
        assert await app.services.users.users.count() == 1

    run(scenario())
    run(app.close())


def test_help_lists_public_commands_hides_admin(make_app):
    app = make_app()

    async def scenario():
        r = await app.router.dispatch(msg("/help"))
        for c in ("/start", "/help", "/profile", "/settings"):
            assert c in r.text
        assert "/admin" not in r.text

    run(scenario())
    run(app.close())


def test_help_shows_admin_commands_to_admin(make_app):
    app = make_app()

    async def scenario():
        r = await app.router.dispatch(msg("/help", uid="admin-1"))
        assert "/admin" in r.text

    run(scenario())
    run(app.close())


def test_settings_validation(make_app):
    app = make_app()

    async def scenario():
        ok = await app.router.dispatch(msg("/settings notify=off"))
        assert "saved" in ok.text.lower()
        bad = await app.router.dispatch(msg("/settings hack=1"))
        assert "Unknown setting" in bad.text
        badval = await app.router.dispatch(msg("/settings notify=maybe"))
        assert "Invalid value" in badval.text

    run(scenario())
    run(app.close())


def test_admin_denied_for_regular_user_and_audited(make_app):
    app = make_app()

    async def scenario():
        r = await app.router.dispatch(msg("/admin stats"))
        assert "permission" in r.text.lower()
        cur = await app.db.conn.execute(
            "SELECT result FROM audit_log ORDER BY id DESC LIMIT 1"
        )
        (result,) = await cur.fetchone()
        assert result == "denied"

    run(scenario())
    run(app.close())


def test_admin_stats_for_admin(make_app):
    app = make_app()

    async def scenario():
        r = await app.router.dispatch(msg("/admin stats", uid="admin-1"))
        assert "Total users" in r.text

    run(scenario())
    run(app.close())


def test_banned_user_rejected(make_app):
    app = make_app()

    async def scenario():
        await app.router.dispatch(msg("/start", uid="bad-1"))
        await app.services.users.users.set_role("eval", "bad-1", "banned")
        r = await app.router.dispatch(msg("/profile", uid="bad-1"))
        assert "revoked" in r.text.lower()

    run(scenario())
    run(app.close())


def test_unknown_command(make_app):
    app = make_app()

    async def scenario():
        r = await app.router.dispatch(msg("/floop"))
        assert "Unknown command" in r.text

    run(scenario())
    run(app.close())
