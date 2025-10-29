# Deploy and Operate

Options
- Docker (single container)
- Docker Compose (DB + bot)
- Kubernetes (manifests provided)

Docker
- Build: `docker build -t ghcr.io/your-org/promo-bot:latest .`
- Run: `docker run --env-file .env -p 8080:8080 ghcr.io/your-org/promo-bot:latest`
- Webhook: ensure reverse proxy forwards to container port 8080.

Docker Compose
- Example bot service (add to `docker-compose.yml`):
```
  bot:
    build: .
    image: ghcr.io/your-org/promo-bot:latest
    env_file: [.env]
    depends_on: [db]
    ports:
      - "8080:8080"  # webhook mode
```
- Start: `docker compose up -d`

Kubernetes (sample)
- Create secret for token: `kubectl create secret generic promo-bot-secrets --from-literal=BOT_TOKEN=xxxx`
- Apply manifests: `kubectl apply -f k8s/`
- Configure Ingress (TLS) to route `/bot` to service.

CD (GitHub Actions → GHCR)
- Workflow: `.github/workflows/docker-publish.yml`
- Needs permissions to write packages (use `GITHUB_TOKEN` with `packages: write`).

Ops
- Health: webhook server responds 200 on `/telegram` and `/metrics`.
- Logs: structured logs in stdout; collect via your platform (e.g., Loki, ELK).
- Migrations: run `alembic upgrade head` on deploy (job or init container).
