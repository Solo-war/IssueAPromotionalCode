from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db.models import PromoIssue, Comment, User


async def main() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is not set")
    engine = create_async_engine(url)
    sf: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    async with sf() as session:
        # Issues by status
        q_issues = await session.execute(
            select(PromoIssue.status, func.count()).where(PromoIssue.issued_at >= week_ago).group_by(PromoIssue.status)
        )
        issues = {row[0]: row[1] for row in q_issues.all()}

        # New users
        q_users = await session.execute(select(func.count()).select_from(User).where(User.created_at >= week_ago))
        new_users = int(q_users.scalar_one())

        # Comments recorded
        q_comments = await session.execute(
            select(func.count()).select_from(Comment).where(Comment.created_at >= week_ago)
        )
        comments = int(q_comments.scalar_one())

    print("Weekly report (last 7 days)")
    print("- New users:", new_users)
    print("- Comments recorded:", comments)
    print("- Promo issues by status:")
    for k in sorted(issues.keys()):
        print(f"  * {k}: {issues[k]}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

