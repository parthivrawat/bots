"""Text normalization tests — pure functions, no platform libs required."""

from bot.adapters.normalize import clean_reddit_text, clean_slack_text


def test_slack_strips_mention():
    assert clean_slack_text("<@U0123> /profile") == "/profile"


def test_slack_bare_word_becomes_command():
    assert clean_slack_text("<@U0123> help") == "/help"


def test_slack_empty_after_strip_defaults_help():
    assert clean_slack_text("<@U0123>") == "/help"


def test_slack_multiple_mentions():
    assert clean_slack_text("<@U1> <@U2> /settings notify=off") == "/settings notify=off"


def test_reddit_strips_username_mention():
    assert clean_reddit_text("u/mybot /help", "mybot") == "/help"


def test_reddit_mention_case_insensitive():
    assert clean_reddit_text("U/MyBot !profile", "mybot") == "!profile"


def test_reddit_does_not_strip_similar_name():
    # 'mybot2' should NOT match the u/mybot word-boundary pattern
    out = clean_reddit_text("u/mybot2 rocks", "mybot")
    assert "mybot2" in out


def test_reddit_plain_text_becomes_command():
    assert clean_reddit_text("u/mybot profile", "mybot") == "/profile"
