from __future__ import annotations

from typing import Optional

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    generate_latest,
    start_http_server,
)

# Counters
PROMO_ISSUE_TOTAL = Counter(
    "promo_issue_total", "Promo issue attempts by status", labelnames=("status",)
)

SUBSCRIPTION_CHECK_TOTAL = Counter(
    "subscription_check_total", "Subscription checks by result", labelnames=("result",)
)

COMMENT_DETECTED_TOTAL = Counter(
    "comment_detected_total", "Comment processing results", labelnames=("recorded",)
)


def inc_promo_issue(status: str) -> None:
    PROMO_ISSUE_TOTAL.labels(status=status).inc()


def inc_subscription(result: bool) -> None:
    SUBSCRIPTION_CHECK_TOTAL.labels(result=str(bool(result)).lower()).inc()


def inc_comment(recorded: bool) -> None:
    COMMENT_DETECTED_TOTAL.labels(recorded=str(bool(recorded)).lower()).inc()


def render_prometheus_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST


def maybe_start_metrics_http_server(host: str, port: int) -> None:
    if port > 0:
        start_http_server(port=port, addr=host)
