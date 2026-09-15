"""Week 3 tests: multi-step conversation state machine."""

from conftest import msg, run


def test_report_workflow_submits(make_app):
    app = make_app()

    async def scenario():
        r1 = await app.router.dispatch(msg("/report"))
        assert "category" in r1.text.lower()

        r2 = await app.router.dispatch(msg("bug"))
        assert "describe" in r2.text.lower()

        r3 = await app.router.dispatch(msg("It does not start."))
        assert "confirm" in r3.text.lower()

        r4 = await app.router.dispatch(msg("yes"))
        assert "submitted" in r4.text.lower()
        assert "bug" in r4.text.lower()

    run(scenario())
    run(app.close())


def test_report_workflow_cancels(make_app):
    app = make_app()

    async def scenario():
        await app.router.dispatch(msg("/report"))
        r = await app.router.dispatch(msg("/cancel"))
        assert "cancelled" in r.text.lower()

        user = await app.services.users.get_or_create("eval", "u1", "tester")
        active = await app.services.state.get_active(user)
        assert active is None

    run(scenario())
    run(app.close())


def test_onboard_workflow_saves_profile(make_app):
    app = make_app()

    async def scenario():
        r1 = await app.router.dispatch(msg("/onboard"))
        assert "city" in r1.text.lower()

        r2 = await app.router.dispatch(msg("Berlin"))
        assert "language" in r2.text.lower()

        r3 = await app.router.dispatch(msg("fr"))
        assert "confirm" in r3.text.lower()

        r4 = await app.router.dispatch(msg("yes"))
        assert "profile updated" in r4.text.lower()
        assert "berlin" in r4.text.lower()
        assert "fr" in r4.text.lower()

        locale = await app.services.users.get_setting(1, "locale")
        city = await app.services.users.get_setting(1, "city")
        assert locale == "fr"
        assert city == "Berlin"

    run(scenario())
    run(app.close())
