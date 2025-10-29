from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from .config import load_settings, validate_settings
from .db.session import create_engine, create_session_factory
from .logging import setup_logging
from .metrics import maybe_start_metrics_http_server
from .middleware.dedup import DedupMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .monitoring import init_sentry
from .services.comments import CommentService
from .services.subscription import SubscriptionService
from .telegram.gateway import TelegramGateway
from .telegram.handlers import create_router
from .webhook import run_webhook


async def main() -> None:
    settings = load_settings()
    setup_logging(level=settings.log_level, json_enabled=settings.log_json)
    init_sentry(settings.sentry_dsn)

    # Validate minimal required configuration for subscription gate
    validate_settings(settings)

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not set")

    bot = Bot(settings.bot_token)
    dp = Dispatcher()

    # DB and services
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    tg_gateway = TelegramGateway(bot, settings.channel_id)
    subscription_service = SubscriptionService(tg_gateway)
    comment_service = CommentService(session_factory, settings)

    # Middlewares: dedup + rate limit
    dp.update.middleware(DedupMiddleware(ttl_seconds=settings.dedup_ttl_seconds))
    dp.update.middleware(
        RateLimitMiddleware(
            user_rate=settings.rate_limit_user_rps,
            user_burst=settings.rate_limit_user_burst,
            global_rate=settings.rate_limit_global_rps,
            global_burst=settings.rate_limit_global_burst,
        )
    )

    dp.include_router(create_router(settings, tg_gateway, comment_service, subscription_service))

    mode = (settings.mode or "polling").lower()
    if mode == "webhook" and settings.webhook_url:
        logging.getLogger(__name__).info("bot_starting", extra={"mode": "webhook"})
        try:
            await run_webhook(dp, bot, settings)
            return
        except Exception as exc:
            logging.getLogger(__name__).warning(
                "webhook_start_failed", extra={"exc": repr(exc), "fallback": "polling"}
            )
    else:
        pass

    # Fallback or explicit polling mode
    # Start a simple Prometheus server if configured
    maybe_start_metrics_http_server(settings.metrics_host, settings.metrics_port)
    logging.getLogger(__name__).info("bot_starting", extra={"mode": "polling"})
    # Development: long polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
