from __future__ import annotations

import logging
import re
from typing import Union

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (  # noqa: F401  # for typing hints if needed in future
    User as TgUser,
)

from ..metrics import inc_subscription
from ..telegram.gateway import TelegramGateway

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Business-layer wrapper for subscription checks.

    Delegates to TelegramGateway.get_chat_member and treats
    member/administrator/creator as valid subscription statuses.
    """

    def __init__(self, tg: TelegramGateway) -> None:
        self._tg = tg

    async def is_subscribed(self, user_id: int) -> bool:
        ok = await self._tg.is_user_subscribed(user_id)
        inc_subscription(ok)
        return ok


def _parse_chat_ref(chat_ref: Union[str, int]) -> Union[str, int]:
    """Accept int id, @username, or t.me URL and return chat id or @username.

    For URLs: try to extract username from https://t.me/<username> or http(s)://telegram.me/<username>.
    If it is a /c/<id>/ style link or joinchat invite, return the original value (Bot API won't accept it for getChatMember).
    """
    if isinstance(chat_ref, int):
        return chat_ref
    s = str(chat_ref).strip()
    # numeric id (e.g., -10012345)
    if re.fullmatch(r"-?\d+", s or ""):
        try:
            return int(s)
        except Exception:
            return s
    # @username
    if s.startswith("@"):
        return s
    # URL patterns -> @username
    m = re.match(r"^https?://(t\.me|telegram\.me)/(?:s/)?([A-Za-z0-9_]{5,})(?:/.*)?$", s)
    if m:
        return f"@{m.group(2)}"
    return s


async def is_subscribed(bot: Bot, user_id: int, chat_ref: Union[str, int]) -> bool:
    """Utility to check membership using getChatMember with robust chat ref parsing.

    Treat statuses in {member, administrator, creator, restricted} as subscribed.
    On any Telegram API error, return False and log.
    """
    target = _parse_chat_ref(chat_ref)
    try:
        member = await bot.get_chat_member(target, user_id)  # type: ignore[arg-type]
        status = getattr(member, "status", None)
        # aiogram v3 may expose enums; normalize to string
        if hasattr(status, "value"):
            status = status.value
        ok = str(status) in {"member", "administrator", "creator", "restricted"}
        inc_subscription(ok)
        return ok
    except TelegramBadRequest as e:
        logger.warning(
            "get_chat_member_failed",
            extra={"exc": repr(e), "chat_ref": str(target), "user_id": user_id},
        )
        inc_subscription(False)
        return False
    except Exception as e:
        logger.warning(
            "get_chat_member_error",
            extra={"exc": repr(e), "chat_ref": str(target), "user_id": user_id},
        )
        inc_subscription(False)
        return False
