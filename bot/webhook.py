from __future__ import annotations

import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from .config import Settings
from .metrics import render_prometheus_metrics

logger = logging.getLogger(__name__)


@web.middleware
async def secret_token_middleware(request: web.Request, handler):
    # Secret token is optional; if set, enforce check
    secret: Optional[str] = request.app.get("webhook_secret")
    if secret:
        header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if header != secret:
            return web.Response(status=401, text="unauthorized")
    return await handler(request)


async def on_startup(app: web.Application) -> None:
    bot: Bot = app["bot"]
    settings: Settings = app["settings"]
    url = settings.webhook_url.rstrip("/") + settings.webhook_path
    await bot.set_webhook(
        url=url,
        secret_token=settings.webhook_secret or None,
        drop_pending_updates=settings.drop_pending_updates,
    )
    logger.info("webhook_set", extra={"url": url})


async def on_cleanup(app: web.Application) -> None:
    bot: Bot = app["bot"]
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("webhook_deleted")
    except Exception as exc:
        logger.warning("webhook_delete_failed", extra={"exc": repr(exc)})


def create_web_app(dp: Dispatcher, bot: Bot, settings: Settings) -> web.Application:
    app = web.Application(middlewares=[secret_token_middleware])
    app["bot"] = bot
    app["settings"] = settings
    app["webhook_secret"] = settings.webhook_secret

    handler = SimpleRequestHandler(dp, bot)
    handler.register(app, path=settings.webhook_path)

    # Metrics endpoint
    metrics_path = "/metrics"

    async def metrics(_request: web.Request) -> web.Response:
        payload, ctype = render_prometheus_metrics()
        return web.Response(body=payload, headers={"Content-Type": ctype})

    app.router.add_get(metrics_path, metrics)

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    setup_application(app, dp, bot=bot)
    return app


async def run_webhook(dp: Dispatcher, bot: Bot, settings: Settings) -> None:
    app = create_web_app(dp, bot, settings)
    logger.info(
        "webhook_server_starting",
        extra={
            "host": settings.webapp_host,
            "port": settings.webapp_port,
            "path": settings.webhook_path,
        },
    )
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.webapp_host, port=settings.webapp_port)
    await site.start()
    # Run forever
    while True:
        await asyncio.sleep(3600)
