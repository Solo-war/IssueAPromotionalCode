# Setup

Prerequisites
- Python 3.11+
- Docker (for Postgres locally)

Steps
1) Copy `.env.example` to `.env` and fill values.
2) Start Postgres: `docker compose up -d db`.
3) Create and activate virtualenv, then `pip install -r requirements.txt`.
4) Run migrations: `alembic upgrade head` (ensure `DATABASE_URL` is set).
5) Choose mode:
   - Polling (dev): leave `MODE=polling` or unset `WEBHOOK_URL`, then run `python -m bot.main`.
   - Webhook (prod): set `MODE=webhook`, `WEBHOOK_URL`, `WEBHOOK_PATH`, `WEBHOOK_SECRET`, and expose the app via reverse proxy to `WEBAPP_HOST:WEBAPP_PORT`. See `docs/WEBHOOK.md`.

Deployment
- Docker (single container): build `docker build -t your/bot:tag .` and run with `--env-file .env`.
- Docker Compose: use the provided `docker-compose.yml` (db service) and add the bot service as below or run the image separately.
- Kubernetes: sample manifests in `k8s/`. Configure secrets (BOT_TOKEN) and env vars.

Monitoring
- Prometheus metrics available at `/metrics` in webhook mode or via a small HTTP server in polling mode.
- Enable polling metrics with `.env`: `METRICS_PORT=9090`.

Docs
- Deployment: `docs/DEPLOY.md`
- Monitoring: `docs/MONITORING.md`
- Webhook: `docs/WEBHOOK.md`

Notes
- Alembic reads `DATABASE_URL`. For async URLs like `postgresql+asyncpg://...`, env.py converts to sync driver for migrations.
- Logging is configured via `LOG_LEVEL` and `LOG_JSON`.
- Aiogram runs long polling by default; webhook can be added later for prod.
