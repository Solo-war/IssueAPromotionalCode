from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.config import Settings
from bot.db.base import Base


@pytest.fixture
def anyio_backend():  # for anyio compatibility if needed
    return "asyncio"


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        bot_token="TEST",
        channel_id="@test",
        database_url="sqlite+aiosqlite:///:memory:",
        promo_code="TEST-CODE",
        promo_total_limit=2,
        promo_per_user_limit=1,
        promo_start_at=None,
        promo_end_at=None,
        active_post_ids=[111, 222],
        log_level="INFO",
        log_json=False,
        sentry_dsn=None,
        mode="polling",
        webhook_url="",
        webhook_path="/telegram",
        webhook_secret=None,
        webapp_host="0.0.0.0",
        webapp_port=8080,
        drop_pending_updates=True,
        rate_limit_user_rps=1.0,
        rate_limit_user_burst=3,
        rate_limit_global_rps=50.0,
        rate_limit_global_burst=100,
        dedup_ttl_seconds=60,
    )
