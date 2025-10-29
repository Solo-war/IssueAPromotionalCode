from __future__ import annotations

import logging
from typing import Optional

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


class TelegramGateway:
    def __init__(self, bot: Bot, channel_id: str) -> None:
        self.bot = bot
        self.channel_id = channel_id

    async def is_user_subscribed(self, user_id: int) -> bool:
        try:
            member = await self.bot.get_chat_member(self.channel_id, user_id)
            status = getattr(member, "status", None)
            # aiogram returns ChatMember* with status being an enum or string depending on version
            if hasattr(status, "value"):
                status = status.value
            allowed = {
                ChatMemberStatus.MEMBER.value,
                ChatMemberStatus.ADMINISTRATOR.value,
                ChatMemberStatus.CREATOR.value,
            }
            # Treat restricted as subscribed too
            try:
                allowed.add(ChatMemberStatus.RESTRICTED.value)  # type: ignore[attr-defined]
            except Exception:
                pass
            return status in allowed
        except TelegramBadRequest as e:
            logger.warning("get_chat_member_failed", extra={"exc": repr(e)})
            return False

    async def send_dm(self, user_id: int, text: str, disable_web_page_preview: bool = True) -> bool:
        try:
            await self.bot.send_message(
                chat_id=user_id, text=text, disable_web_page_preview=disable_web_page_preview
            )
            return True
        except TelegramBadRequest as e:
            logger.warning("send_dm_failed", extra={"exc": repr(e), "user_id": user_id})
            return False
