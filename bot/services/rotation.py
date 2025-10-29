from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..db.models import Config


class PostRotationManager:
    """
    Manages the list of active post ids with constraints:
    - max items: 5
    - update no more than once per 7 days unless forced
    - archives previous list to `archived_post_ids`
    Stores values in Config table as JSON.
    Keys used: `active_post_ids`, `active_posts_updated_at`, `archived_post_ids`
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def get_active_posts(self) -> list[int]:
        async with self._sf() as session:
            cfg = await session.get(Config, "active_post_ids")
            if not cfg or not cfg.value:
                return []
            try:
                return [int(x) for x in json.loads(cfg.value)]
            except Exception:
                return []

    async def set_active_posts(
        self, post_ids: Iterable[int], force: bool = False
    ) -> tuple[bool, str]:
        items = list(dict.fromkeys(int(x) for x in post_ids))  # de-dup, keep order
        if len(items) > 5:
            return False, "Active posts limit exceeded (max 5)"

        async with self._sf() as session:
            # Rate limit weekly updates
            updated_at_cfg = await session.get(Config, "active_posts_updated_at")
            now = datetime.now(timezone.utc)
            if updated_at_cfg and updated_at_cfg.value:
                try:
                    last = datetime.fromisoformat(updated_at_cfg.value)
                except Exception:
                    last = None
                if last and (now - last) < timedelta(days=7) and not force:
                    return False, "Updates allowed no more than once per 7 days"

            # Archive previous
            prev_cfg = await session.get(Config, "active_post_ids")
            prev_list: list[int] = []
            if prev_cfg and prev_cfg.value:
                try:
                    prev_list = [int(x) for x in json.loads(prev_cfg.value)]
                except Exception:
                    prev_list = []
            archived_cfg = await session.get(Config, "archived_post_ids")
            archived: list[int] = []
            if archived_cfg and archived_cfg.value:
                try:
                    archived = [int(x) for x in json.loads(archived_cfg.value)]
                except Exception:
                    archived = []
            archived = list(dict.fromkeys(prev_list + archived))

            # Persist new values
            new_cfg = prev_cfg or Config(key="active_post_ids", value=None)
            new_cfg.value = json.dumps(items)
            session.add(new_cfg)

            updated_at_cfg = updated_at_cfg or Config(key="active_posts_updated_at", value=None)
            updated_at_cfg.value = now.isoformat()
            session.add(updated_at_cfg)

            archived_cfg = archived_cfg or Config(key="archived_post_ids", value=None)
            archived_cfg.value = json.dumps(archived)
            session.add(archived_cfg)

            await session.commit()
            return True, "Active posts updated"
