from __future__ import annotations

import logging
from typing import Optional


def init_sentry(dsn: Optional[str]) -> None:
    if not dsn:
        return
    try:
        import sentry_sdk  # type: ignore

        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.0)
        logging.getLogger(__name__).info("sentry_initialized")
    except Exception as exc:  # pragma: no cover
        logging.getLogger(__name__).warning("sentry_init_failed", exc=exc)
