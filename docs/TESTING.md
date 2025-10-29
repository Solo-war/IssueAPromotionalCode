# Testing Guide

Commands
- Install: `pip install -r requirements.txt`
- Run unit tests: `pytest`
- Run with verbose and markers: `pytest -q -m "not load"`
- Run load tests: `RUN_LOAD_TESTS=1 pytest -m load`

What’s covered
- Subscription: unit test with a fake Telegram gateway.
- Comments: async DB tests (SQLite in-memory) for recording and checking.
- Promo: issuing with idempotency and total limit.
- E2E flow: user subscribes, comments, gets promo (service-level integration, no network).
- Load-like: optional test issuing to many users (skipped by default).

Notes
- Tests use SQLite + aiosqlite for speed; production DB is PostgreSQL.
- pytest-asyncio is configured via `pyproject.toml` with `asyncio_mode=auto`.
