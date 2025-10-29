# Webhook, Security, and Limits

This project supports both webhook (HTTPS) and polling. For production, use webhook with a reverse proxy and a secret token.

Requirements
- Public domain with valid TLS (Let’s Encrypt via certbot, or managed certs)
- Reverse proxy (Nginx/Caddy/Traefik) that forwards to the bot app
- Set environment in `.env` (examples below)

Env keys
- `MODE=webhook`
- `WEBHOOK_URL=https://your.domain.tld/bot` (no trailing slash)
- `WEBHOOK_PATH=/telegram` (full path becomes `/bot/telegram`)
- `WEBHOOK_SECRET=<random 32-64 chars>`
- `WEBAPP_HOST=0.0.0.0`, `WEBAPP_PORT=8080`
- `DROP_PENDING_UPDATES=true`

Run
- Install deps and run the app: `python -m bot.main`
- Reverse proxy forwards `https://your.domain.tld/bot/telegram` → `http://127.0.0.1:8080/telegram`
- On startup, the bot sets webhook with the secret token; requests without correct header are rejected (401).

Nginx example
```
server {
    listen 80;
    server_name your.domain.tld;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://$host$request_uri; }
}

server {
    listen 443 ssl;
    server_name your.domain.tld;
    ssl_certificate /etc/letsencrypt/live/your.domain.tld/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your.domain.tld/privkey.pem;

    location /bot/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

Caddy example
```
your.domain.tld {
    route /bot* {
        uri strip_prefix /bot
        reverse_proxy 127.0.0.1:8080
    }
}
```

Certbot (Let’s Encrypt)
- Nginx: `sudo certbot --nginx -d your.domain.tld`
- Standalone + Nginx reload: `sudo certbot certonly --webroot -w /var/www/certbot -d your.domain.tld`

Security
- Secret token: Telegram sends `X-Telegram-Bot-Api-Secret-Token`. The server validates it.
- Keep `BOT_TOKEN` in environment or secrets manager (GitHub Actions → Settings → Secrets → Actions → `BOT_TOKEN`). Never commit tokens.
- Optional: IP allowlist on proxy to Telegram IP ranges (see Telegram docs) and rate limit at proxy level (e.g., `limit_req` in Nginx).

Limits and anti-spam
- Per-user and global token-bucket middleware throttle requests. Configure via `.env`:
  - `RATE_LIMIT_USER_RPS`, `RATE_LIMIT_USER_BURST`
  - `RATE_LIMIT_GLOBAL_RPS`, `RATE_LIMIT_GLOBAL_BURST`
- Deduplication middleware drops duplicate Message/CallbackQuery within `DEDUP_TTL_SECONDS`.
- Business-level idempotency (e.g., one promo per user) is enforced in the DB schema.

Fallback to polling
- If `MODE` is not `webhook` or `WEBHOOK_URL` is empty, the bot runs long polling (`dp.start_polling`). Useful for local dev.

Troubleshooting
- Check logs for `webhook_set` on startup and `webhook_server_starting` with host/port/path.
- Verify reverse proxy path matches `WEBHOOK_URL + WEBHOOK_PATH`.
- 401 responses: ensure `WEBHOOK_SECRET` matches the bot’s configured secret.
