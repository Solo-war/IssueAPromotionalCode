from __future__ import annotations

import logging

from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..config import Settings
from ..services.subscription import is_subscribed
from ..telegram.gateway import TelegramGateway  # kept for DI compatibility
from ..texts import (
    BUTTON_CHECK_SUB,
    BUTTON_OPEN_CHANNEL,
    GREETING_TEXT,
    REPLY_NOT_SUBSCRIBED,
    REPLY_SUCCESS,
    SUBSCRIPTION_PROMPT_TEXT,
)

logger = logging.getLogger(__name__)


def _subscription_keyboard(open_url: str | None) -> types.InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if open_url:
        kb.button(text=BUTTON_OPEN_CHANNEL, url=open_url)
    kb.button(text=BUTTON_CHECK_SUB, callback_data="check_sub")
    kb.adjust(1)
    return kb.as_markup()


def create_router(
    settings: Settings,
    tg_gateway: TelegramGateway,  # unused, preserved to avoid breaking DI
    comment_service,  # unused legacy param
    subscription_service,  # unused legacy param
) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def on_start(message: types.Message) -> None:  # type: ignore[no-redef]
        await message.answer(GREETING_TEXT)
        await message.answer(
            SUBSCRIPTION_PROMPT_TEXT,
            reply_markup=_subscription_keyboard(settings.subscription_url or None),
            disable_web_page_preview=True,
        )

    @router.callback_query(F.data == "check_sub")
    async def on_check_sub(callback: types.CallbackQuery) -> None:  # type: ignore[no-redef]
        try:
            await callback.answer()
        except Exception:
            pass
        user_id = callback.from_user.id if callback.from_user else None  # type: ignore[union-attr]
        if not user_id:
            return
        ok = await is_subscribed(callback.message.bot, user_id, settings.subscription_target or "")  # type: ignore[union-attr]
        if ok:
            link: str | None = settings.private_group_invite_link or None
            if not link and settings.private_group_id is not None:
                try:
                    # Prefer exportChatInviteLink; fallback to createChatInviteLink
                    bot = callback.message.bot  # type: ignore[union-attr]
                    if hasattr(bot, "export_chat_invite_link"):
                        link = await bot.export_chat_invite_link(settings.private_group_id)
                    elif hasattr(bot, "create_chat_invite_link"):
                        res = await bot.create_chat_invite_link(settings.private_group_id)
                        link = getattr(res, "invite_link", None)
                except Exception as exc:
                    logger.warning("invite_link_generation_failed", extra={"exc": repr(exc)})
                    link = None
            if link:
                await callback.message.answer(REPLY_SUCCESS.format(link=link))  # type: ignore[union-attr]
            else:
                await callback.message.answer(
                    "Не удалось получить инвайт-ссылку. Проверьте права бота и настройки."
                )  # type: ignore[union-attr]
        else:
            await callback.message.answer(
                REPLY_NOT_SUBSCRIBED,
                reply_markup=_subscription_keyboard(settings.subscription_url or None),
                disable_web_page_preview=True,
            )  # type: ignore[union-attr]

    return router
