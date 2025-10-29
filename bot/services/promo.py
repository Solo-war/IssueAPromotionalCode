from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Tuple

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..config import Settings
from ..db.models import PromoIssue
from ..metrics import inc_promo_issue

IssueStatus = Literal["issued", "already_issued", "exhausted", "inactive", "invalid"]


@dataclass
class IssueResult:
    status: IssueStatus
    code: str | None = None


class PromoService:
    """Service that controls issuing a promo code with idempotency and limits."""

    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], settings: Settings
    ) -> None:
        self._sf = session_factory
        self._code = settings.promo_code
        self._total_limit = int(settings.promo_total_limit)
        self._per_user_limit = int(settings.promo_per_user_limit)
        self._start_at = settings.promo_start_at
        self._end_at = settings.promo_end_at

    async def _time_active(self) -> bool:
        now = datetime.now(timezone.utc)
        if self._start_at and now < self._start_at:
            return False
        if self._end_at and now > self._end_at:
            return False
        return True

    async def can_issue(self, user_id: int) -> Tuple[bool, IssueStatus]:
        if not self._code:
            return False, "invalid"
        if not await self._time_active():
            return False, "inactive"
        async with self._sf() as session:
            # per-user idempotency
            existing = await session.execute(
                select(PromoIssue.id).where(
                    PromoIssue.user_id == user_id, PromoIssue.code == self._code
                )
            )
            if existing.first() is not None:
                return False, "already_issued"
            # total limit
            total = await session.execute(
                select(func.count()).select_from(PromoIssue).where(PromoIssue.code == self._code)
            )
            count = int(total.scalar_one())
            if count >= self._total_limit:
                return False, "exhausted"
        return True, "issued"

    async def issue(self, user_id: int) -> IssueResult:
        ok, reason = await self.can_issue(user_id)
        if not ok:
            inc_promo_issue(reason)
            return IssueResult(status=reason, code=None)
        async with self._sf() as session:
            try:
                obj = PromoIssue(user_id=user_id, code=self._code, status="issued", source="auto")
                session.add(obj)
                await session.commit()
                inc_promo_issue("issued")
                return IssueResult(status="issued", code=self._code)
            except IntegrityError:
                # Unique constraint hit: treat as already issued
                await session.rollback()
                inc_promo_issue("already_issued")
                return IssueResult(status="already_issued", code=self._code)
