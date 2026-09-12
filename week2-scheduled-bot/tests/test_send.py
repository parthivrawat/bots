"""Tests for proactive message delivery via App.send_to_user()."""

from bot.core.contracts import User

from conftest import run


class FakeAdapter:
    platform = "eval"

    def __init__(self):
        self.sent = []

    async def send(self, user, message):
        self.sent.append((user, message))


def test_send_to_user_routes_to_matching_adapter(make_app):
    app = make_app()
    fake = FakeAdapter()
    app.adapters = [fake]

    user = User(
        id=1,
        platform="eval",
        platform_user_id="u1",
        username="tester",
        role="user",
    )

    async def scenario():
        await app.send_to_user(user, "hello from a job")

    run(scenario())
    run(app.close())

    assert len(fake.sent) == 1
    assert fake.sent[0][0].platform_user_id == "u1"
    assert fake.sent[0][1] == "hello from a job"
