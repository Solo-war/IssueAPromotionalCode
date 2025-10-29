from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_list(value: str | None) -> List[int]:
    if not value:
        return []
    parts = [p.strip() for p in value.split(",") if p.strip()]
    out: List[int] = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            continue
    return out


@dataclass
class Settings:
    bot_token: str
    channel_id: str
    database_url: str

    promo_code: str
    promo_total_limit: int
    promo_per_user_limit: int
    promo_start_at: Optional[datetime]
    promo_end_at: Optional[datetime]
    active_post_ids: List[int]

    log_level: str = "INFO"
    log_json: bool = False
    sentry_dsn: Optional[str] = None

    # Webhook
    mode: str = "polling"  # "polling" or "webhook"
    webhook_url: str = ""
    webhook_path: str = "/telegram"
    webhook_secret: Optional[str] = None
    webapp_host: str = "0.0.0.0"
    webapp_port: int = 8080
    drop_pending_updates: bool = True

    # Limits / dedup
    rate_limit_user_rps: float = 1.0
    rate_limit_user_burst: int = 3
    rate_limit_global_rps: float = 50.0
    rate_limit_global_burst: int = 100
    dedup_ttl_seconds: int = 120

    # Metrics for polling mode (a simple built-in HTTP server)
    metrics_host: str = "0.0.0.0"
    metrics_port: int = 0  # 0 disables the extra server

    # Subscription-gate configuration
    # Chat to check subscription in (int id, @username or URL)
    subscription_target: Optional[str] = None
    # URL for the "Open channel" button
    subscription_url: Optional[str] = None
    # Either a fixed invite link, or a private group id to generate link
    private_group_invite_link: Optional[str] = None
    private_group_id: Optional[int] = None


def load_settings() -> Settings:
    load_dotenv(override=False)

    start_at = os.getenv("PROMO_START_AT")
    end_at = os.getenv("PROMO_END_AT")

    def parse_dt(val: str | None) -> Optional[datetime]:
        if not val:
            return None
        try:
            # Expect ISO 8601 with Z or timezone-naive
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None

    return Settings(
        bot_token=os.environ.get("BOT_TOKEN", ""),
        channel_id=os.environ.get("CHANNEL_ID", ""),
        database_url=os.environ.get("DATABASE_URL", ""),
        promo_code=os.environ.get("PROMO_CODE", "SPRING-INSPIRE-2024"),
        promo_total_limit=int(os.environ.get("PROMO_TOTAL_LIMIT", "200")),
        promo_per_user_limit=int(os.environ.get("PROMO_PER_USER_LIMIT", "1")),
        promo_start_at=parse_dt(start_at),
        promo_end_at=parse_dt(end_at),
        active_post_ids=_parse_list(os.environ.get("ACTIVE_POST_IDS")),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
        log_json=_parse_bool(os.environ.get("LOG_JSON"), default=False),
        sentry_dsn=os.environ.get("SENTRY_DSN"),
        mode=os.environ.get("MODE", "polling").lower(),
        webhook_url=os.environ.get("WEBHOOK_URL", ""),
        webhook_path=os.environ.get("WEBHOOK_PATH", "/telegram"),
        webhook_secret=os.environ.get("WEBHOOK_SECRET") or None,
        webapp_host=os.environ.get("WEBAPP_HOST", "0.0.0.0"),
        webapp_port=int(os.environ.get("WEBAPP_PORT", "8080")),
        drop_pending_updates=_parse_bool(os.environ.get("DROP_PENDING_UPDATES"), default=True),
        rate_limit_user_rps=float(os.environ.get("RATE_LIMIT_USER_RPS", "1")),
        rate_limit_user_burst=int(os.environ.get("RATE_LIMIT_USER_BURST", "3")),
        rate_limit_global_rps=float(os.environ.get("RATE_LIMIT_GLOBAL_RPS", "50")),
        rate_limit_global_burst=int(os.environ.get("RATE_LIMIT_GLOBAL_BURST", "100")),
        dedup_ttl_seconds=int(os.environ.get("DEDUP_TTL_SECONDS", "120")),
        metrics_host=os.environ.get("METRICS_HOST", "0.0.0.0"),
        metrics_port=int(os.environ.get("METRICS_PORT", "0")),
        subscription_target=os.environ.get("SUBSCRIPTION_TARGET") or None,
        subscription_url=os.environ.get("SUBSCRIPTION_URL") or None,
        private_group_invite_link=(os.environ.get("PRIVATE_GROUP_INVITE_LINK") or None),
        private_group_id=(
            int(os.environ["PRIVATE_GROUP_ID"]) if os.environ.get("PRIVATE_GROUP_ID") else None
        ),
    )


def validate_settings(settings: Settings) -> None:
    """Validate minimal required configuration for subscription-gate.

    Requires SUBSCRIPTION_TARGET and at least one of PRIVATE_GROUP_INVITE_LINK or PRIVATE_GROUP_ID.
    """
    sub_target = (settings.subscription_target or "").strip()
    if not sub_target:
        raise RuntimeError("SUBSCRIPTION_TARGET is not set; must be chat id, @username or URL")
    if not (settings.private_group_invite_link or settings.private_group_id):
        raise RuntimeError("One of PRIVATE_GROUP_INVITE_LINK or PRIVATE_GROUP_ID must be set")
