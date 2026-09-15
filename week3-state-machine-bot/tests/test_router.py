import pytest

from bot.core.errors import UnknownCommand
from bot.core.router import Router


def test_parse_slash_command():
    cmd = Router.parse("/settings timezone=UTC")
    assert cmd.name == "settings"
    assert cmd.kwargs == {"timezone": "UTC"}
    assert cmd.args == []


def test_parse_bang_and_botname_suffix():
    cmd = Router.parse("!help@MyBot")
    assert cmd.name == "help"


def test_parse_positional_args():
    cmd = Router.parse("/admin ban telegram:42")
    assert cmd.name == "admin"
    assert cmd.args == ["ban", "telegram:42"]


def test_parse_empty_raises():
    with pytest.raises(UnknownCommand):
        Router.parse("/")


def test_parse_mixed_tokens():
    cmd = Router.parse("/note add title=Hello World now")
    assert cmd.name == "note"
    assert cmd.args == ["add", "World", "now"]
    assert cmd.kwargs == {"title": "Hello"}
