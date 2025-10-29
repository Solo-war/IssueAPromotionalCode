from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional

from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware


class DedupMiddleware(BaseMiddleware):
    """Deduplicate repeated updates in a short time window.

    In-memory TTL set keyed by message identity. Intended as best-effort protection.
    """

    def __init__(self, ttl_seconds: int = 120) -> None:
        super().__init__()
        self._ttl = ttl_seconds
        self._seen: Dict[str, float] = {}

    def _make_key(self, event: types.TelegramObject) -> Optional[str]:
        if isinstance(event, types.Message):
            chat_id = getattr(event.chat, "id", None)
            mid = getattr(event, "message_id", None)
            if chat_id is not None and mid is not None:
                return f"msg:{chat_id}:{mid}"
        if isinstance(event, types.CallbackQuery):
            cid = getattr(event, "id", None)
            if cid is not None:
                return f"cb:{cid}"
        return None

    def _sweep(self, now: float) -> None:
        # Remove expired entries
        expired = [k for k, ts in self._seen.items() if now - ts > self._ttl]
        for k in expired:
            self._seen.pop(k, None)

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Any],
        event: types.TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        now = time.monotonic()
        self._sweep(now)
        key = self._make_key(event)
        if key:
            if key in self._seen:
                # Drop duplicate silently
                return
            self._seen[key] = now
        return await handler(event, data)
