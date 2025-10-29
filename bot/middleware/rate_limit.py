from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple

from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware


@dataclass
class _TokenBucket:
    rate: float  # tokens per second
    burst: int  # bucket capacity
    tokens: float
    last: float

    def allow(self, now: float) -> bool:
        # Refill tokens
        elapsed = max(0.0, now - self.last)
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


class RateLimitMiddleware(BaseMiddleware):
    """Simple in-memory token bucket limiter.

    - Per-user limiter (from_user.id)
    - Global limiter
    If a user exceeds the limit, message is ignored and optional warning is sent once per cooldown.
    """

    def __init__(
        self,
        user_rate: float = 1.0,
        user_burst: int = 3,
        global_rate: float = 50.0,
        global_burst: int = 100,
    ) -> None:
        super().__init__()
        self._user_rate = user_rate
        self._user_burst = user_burst
        self._global = _TokenBucket(
            global_rate, global_burst, tokens=global_burst, last=time.monotonic()
        )
        self._users: Dict[int, _TokenBucket] = {}
        self._warned: Dict[int, float] = {}
        self._lock = asyncio.Lock()

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, Dict[str, Any]], Any],
        event: types.TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        now = time.monotonic()
        user = data.get("event_from_user")
        uid: Optional[int] = getattr(user, "id", None) if user else None

        async with self._lock:
            # Global check
            if not self._global.allow(now):
                return  # silently drop to protect resources

            # Per-user check
            if uid is not None:
                bucket = self._users.get(uid)
                if bucket is None:
                    bucket = _TokenBucket(
                        self._user_rate, self._user_burst, tokens=self._user_burst, last=now
                    )
                    self._users[uid] = bucket
                allowed = bucket.allow(now)
            else:
                allowed = True

        if not allowed:
            if isinstance(event, types.Message):
                last_warn = self._warned.get(uid or 0, 0.0)
                if now - last_warn > 5.0:  # avoid spamming warnings
                    self._warned[uid or 0] = now
                    try:
                        await event.answer("Слишком часто. Пожалуйста, подождите пару секунд.")
                    except Exception:
                        pass
            return

        return await handler(event, data)
