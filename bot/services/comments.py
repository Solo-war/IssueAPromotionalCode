from __future__ import annotations

import json
from typing import Iterable, Sequence

from aiogram import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..config import Settings
from ..db.models import Comment, Config, User
from ..metrics import inc_comment


def _first_text(message: types.Message) -> str | None:
    if message.text:
        return message.text[:512]
    if message.caption:
        return message.caption[:512]
    return None


class CommentService:
    """
    Records comments that belong to specific channel posts (via linked discussion group).

    We treat Message.message_thread_id as the identifier of the channel post's
    discussion topic. Only messages with thread_id that is in the configured
    active post ids are recorded.
    """

    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], settings: Settings
    ) -> None:
        self._sf = session_factory
        # Settings provides initial list. Rotation manager (optional) can override via Config table.
        self._initial_active_post_ids = list(settings.active_post_ids)

    async def _load_active_post_ids(self, session: AsyncSession) -> list[int]:
        cfg = await session.get(Config, "active_post_ids")
        if not cfg or not cfg.value:
            return list(self._initial_active_post_ids)
        try:
            ids = json.loads(cfg.value)
            if isinstance(ids, list):
                return [int(x) for x in ids if isinstance(x, (int, str)) and str(x).isdigit()]
        except Exception:
            pass
        return list(self._initial_active_post_ids)

    async def record_group_message(self, message: types.Message) -> bool:
        """
        Persist a comment if it belongs to an active post thread.

        Returns True if recorded or already existed, False if ignored.
        """
        if message.chat.type not in {"group", "supergroup"}:
            return False

        thread_id = message.message_thread_id
        if not thread_id:
            # Not a topic message tied to a channel post
            return False

        async with self._sf() as session:
            active_ids = set(await self._load_active_post_ids(session))
            if active_ids and int(thread_id) not in active_ids:
                return False

            # Ensure user row exists
            user_id = int(message.from_user.id) if message.from_user else None  # type: ignore[union-attr]
            if not user_id:
                return False

            await self._ensure_user(session, message)

            # Upsert comment for (user_id, post_id)
            existing = await session.execute(
                select(Comment).where(Comment.user_id == user_id, Comment.post_id == int(thread_id))
            )
            row = existing.scalar_one_or_none()
            if row is None:
                row = Comment(
                    user_id=user_id,
                    post_id=int(thread_id),
                    message_id=int(message.message_id),
                    thread_id=int(thread_id),
                    text_snippet=_first_text(message),
                )
                session.add(row)
                await session.commit()
                inc_comment(True)
                return True
            else:
                # Already recorded
                inc_comment(True)
                return True

    async def has_commented_in_active_posts(self, user_id: int) -> bool:
        async with self._sf() as session:
            active_ids = await self._load_active_post_ids(session)
            if not active_ids:
                inc_comment(False)
                return False
            res = await session.execute(
                select(Comment.id).where(
                    Comment.user_id == user_id, Comment.post_id.in_(active_ids)
                )
            )
            return res.first() is not None

    async def _ensure_user(self, session: AsyncSession, message: types.Message) -> None:
        tg = message.from_user
        if not tg:
            return
        user_id = int(tg.id)
        obj = await session.get(User, user_id)
        if obj is None:
            obj = User(
                user_id=user_id,
                username=tg.username,
                first_name=tg.first_name,
                last_name=tg.last_name,
                lang=tg.language_code,
            )
            session.add(obj)
        else:
            # Update profile info if changed
            obj.username = tg.username
            obj.first_name = tg.first_name
            obj.last_name = tg.last_name
            obj.lang = tg.language_code
        await session.commit()
