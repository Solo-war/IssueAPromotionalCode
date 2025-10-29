Subscription Gateway Bot (aiogram v3)

A minimal Telegram bot that acts as a subscription gate:

- Flow: `/start` → greeting → request to subscribe → two buttons → check membership → send invite link to a private group.
- Keeps infrastructure intact (config via .env, logging, middlewares, health/webhook, DI wiring) while removing legacy promo/comment flows.

Run
- Copy `.env.example` to `.env` and fill values (see below).
- Install dependencies: `pip install -r requirements.txt`
- Start in polling mode: `python -m bot.main`

Webhook mode is supported via `MODE=webhook` (see `.env.example`).

Required Bot Permissions
- To check membership in a private group/channel, the bot must be a member with permission to read member list.
- If you use `PRIVATE_GROUP_ID` (dynamic invite generation), the bot must be an administrator in that target chat.

Environment Variables
- `BOT_TOKEN` — Telegram Bot token.
- `SUBSCRIPTION_TARGET` — chat to check membership in. Accepts int id (e.g. `-100123...`), `@username`, or URL `https://t.me/<username>`.
- `SUBSCRIPTION_URL` — URL for the “Открыть канал” button (optional).
- Access options (choose one):
  - `PRIVATE_GROUP_INVITE_LINK` — fixed invite link to a private chat.
  - `PRIVATE_GROUP_ID` — numeric id of the private chat to generate a fresh invite via `exportChatInviteLink`.

Validation at startup: `SUBSCRIPTION_TARGET` must be set and at least one of `PRIVATE_GROUP_INVITE_LINK` or `PRIVATE_GROUP_ID`.

User Flow
- `/start` shows greeting and a message with two buttons: “Открыть канал” and “Проверить подписку”.
- Tapping “Проверить подписку” runs `getChatMember`. If member in {member, administrator, creator, restricted} → considered subscribed.
- If subscribed → bot responds with the invite link.
- If not subscribed → bot prompts to subscribe and shows the same buttons.

Notes
- Framework: aiogram v3.x
- Middlewares retained: dedup and rate-limit
- Metrics endpoint preserved (Prometheus). Webhook server unchanged.

Запуск в Docker (RU)
- Polling (проще всего):
  - Убедитесь, что в `.env` задан `MODE=polling` (или переменная отсутствует).
  - Сборка: `docker build -t subscription-gate .`
  - Запуск: `docker run --rm --name subscription-gate --env-file .env subscription-gate`

- Webhook (если нужен внешний доступ):
  - В `.env` укажите: `MODE=webhook`, `WEBHOOK_URL=https://your.domain.tld/bot`, `WEBAPP_HOST=0.0.0.0`, `WEBAPP_PORT=8080`.
  - Запуск с портом: `docker run --rm --name subscription-gate -p 8080:8080 --env-file .env subscription-gate`
  - Нужен обратный прокси/SSL, чтобы Telegram мог достучаться до `WEBHOOK_URL`.

- Docker Compose (бот + локальная БД):
  - В `docker-compose.yml` уже описаны сервисы `db` (Postgres) и `bot`.
  - Для бота в compose переопределяется `DATABASE_URL` на `postgresql+asyncpg://postgres:postgres@db:5432/promo` (подключение по имени сервиса `db`).
  - Команды: `docker compose build` и `docker compose up -d`
  - Логи бота: `docker compose logs -f bot`

Чек-лист переменных окружения
- Обязательные: `BOT_TOKEN`, `SUBSCRIPTION_TARGET`, и один из `PRIVATE_GROUP_INVITE_LINK` или `PRIVATE_GROUP_ID`.
- Рекомендуется: `SUBSCRIPTION_URL` для кнопки «Открыть канал».
- Права: для генерации инвайта по `PRIVATE_GROUP_ID` бот должен быть админом в целевом чате.
