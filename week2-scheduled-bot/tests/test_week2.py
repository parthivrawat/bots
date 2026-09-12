"""Week 2 tests: scheduled jobs, subscriptions, and price alerts."""

from conftest import msg, run


def test_subscribe_and_unsubscribe_weather(make_app):
    app = make_app()

    async def scenario():
        r = await app.router.dispatch(msg("/subscribe weather"))
        assert "subscribed" in r.text.lower()
        assert "weather" in r.text.lower()

        # eval user is the first user, so id is 1
        setting = await app.services.users.users.get_setting(1, "weather_report")
        assert setting == "on"

        r2 = await app.router.dispatch(msg("/unsubscribe weather"))
        assert "unsubscribed" in r2.text.lower()

    run(scenario())
    run(app.close())


def test_alert_create_list_and_cancel(make_app):
    app = make_app()

    async def scenario():
        create = await app.router.dispatch(msg("/alert BTC above 50000"))
        assert "alert created" in create.text.lower()
        assert "BTC" in create.text

        alerts = await app.router.dispatch(msg("/alerts"))
        assert "BTC" in alerts.text
        assert "$50,000.00" in alerts.text

        cancel = await app.router.dispatch(msg("/alert cancel 1"))
        assert "cancelled" in cancel.text.lower()

        empty = await app.router.dispatch(msg("/alerts"))
        assert "no price alerts" in empty.text.lower()

    run(scenario())
    run(app.close())


def test_admin_jobs_lists_registered_jobs(make_app):
    app = make_app()

    async def scenario():
        r = await app.router.dispatch(msg("/admin jobs", uid="admin-1"))
        assert "daily_weather" in r.text
        assert "price_alerts" in r.text
        assert "health_check" in r.text

    run(scenario())
    run(app.close())


def test_admin_job_disable_enable_and_trigger(make_app):
    app = make_app()

    async def scenario():
        disable = await app.router.dispatch(msg("/admin job health_check disable", uid="admin-1"))
        assert "disabled" in disable.text.lower()

        job = await app.services.jobs.get_job("health_check")
        assert not job.enabled

        enable = await app.router.dispatch(msg("/admin job health_check enable", uid="admin-1"))
        assert "enabled" in enable.text.lower()

        job = await app.services.jobs.get_job("health_check")
        assert job.enabled

        trigger = await app.router.dispatch(msg("/admin job health_check trigger", uid="admin-1"))
        assert "triggered" in trigger.text.lower()
        assert "healthy" in trigger.text.lower() or "unhealthy" in trigger.text.lower()

    run(scenario())
    run(app.close())
