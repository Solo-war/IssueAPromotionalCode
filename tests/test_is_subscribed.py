from __future__ import annotations

import types as pytypes

import pytest

from bot.services.subscription import is_subscribed


class FakeMember:
    def __init__(self, status: str):
        self.status = status


class FakeBot:
    def __init__(self, status: str | Exception):
        self._status = status

    async def get_chat_member(self, chat_id, user_id):  # noqa: D401
        if isinstance(self._status, Exception):
            raise self._status
        return FakeMember(self._status)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,expected",
    [
        ("member", True),
        ("administrator", True),
        ("creator", True),
        ("restricted", True),
        ("left", False),
        ("kicked", False),
    ],
)
async def test_is_subscribed_statuses(status, expected):
    bot = FakeBot(status)
    assert await is_subscribed(bot, 123, "@test") is expected


@pytest.mark.asyncio
async def test_is_subscribed_telegram_error():
    class DummyError(Exception):
        pass

    bot = FakeBot(DummyError("fail"))
    assert await is_subscribed(bot, 123, "@test") is False
