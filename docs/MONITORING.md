# Monitoring & Metrics

Prometheus metrics (exported)
- `promo_issue_total{status}` — attempts to issue promo code by status: `issued`, `already_issued`, `exhausted`, `inactive`, `invalid`.
- `subscription_check_total{result}` — subscription checks with `true|false`.
- `comment_detected_total{recorded}` — group messages under discussions processed; `true` when recorded.

Endpoints
- Webhook mode: `/metrics` served by aiohttp.
- Polling mode: optional tiny HTTP server; enable via `.env`:
  - `METRICS_HOST=0.0.0.0`
  - `METRICS_PORT=9090`

Dashboards
- Suggested panels: total issues by status (stacked), subscription true/false ratio, comments recorded rate, 95p issue latency (if added later).

Alerts (examples)
- No `promo_issue_total{status="issued"}` increment in 30m.
- High `subscription_check_total{result="false"}` share (>80%).
- Rapid increase in `comment_detected_total{recorded="false"}`.
