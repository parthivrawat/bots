import time

from conftest import msg, run


def test_rate_limiter_trips_after_burst(make_app):
    # capacity=3, refill of 1 token per 60s -> no meaningful refill during test
    app = make_app(rate_limit_capacity=3, rate_limit_window_s=60)

    async def scenario():
        replies = [await app.router.dispatch(msg("/help")) for _ in range(3)]
        assert all("commands" in r.text.lower() for r in replies)

        blocked = await app.router.dispatch(msg("/help"))
        assert "too fast" in blocked.text.lower()

    run(scenario())
    run(app.close())


def test_rate_limiter_recovers_after_window(make_app):
    # capacity=1, refill 1 token per 0.5s: second immediate call blocks,
    # a call after the window succeeds.
    app = make_app(rate_limit_capacity=1, rate_limit_window_s=0.5)

    async def scenario():
        await app.router.dispatch(msg("/help"))
        blocked = await app.router.dispatch(msg("/help"))
        assert "too fast" in blocked.text.lower()

        time.sleep(0.6)
        recovered = await app.router.dispatch(msg("/help"))
        assert "commands" in recovered.text.lower()

    run(scenario())
    run(app.close())


def test_rate_limit_is_per_user(make_app):
    app = make_app(rate_limit_capacity=1, rate_limit_window_s=60)

    async def scenario():
        await app.router.dispatch(msg("/help", uid="u-a"))
        blocked_a = await app.router.dispatch(msg("/help", uid="u-a"))
        assert "too fast" in blocked_a.text.lower()
        ok_b = await app.router.dispatch(msg("/help", uid="u-b"))
        assert "commands" in ok_b.text.lower()

    run(scenario())
    run(app.close())
