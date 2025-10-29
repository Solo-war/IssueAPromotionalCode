# QA Checklist

Scope: Telegram bot that issues a promo code after subscription + comment.

Preconditions
- Bot token configured; bot added to linked discussion group.
- Active post(s) configured (`ACTIVE_POST_IDS`).
- Promo code set and valid window/limits.

Functional checks
- /start: bot responds with clear instructions.
- Subscription check:
  - Subscribed user proceeds; unsubscribed user gets guidance.
- Comment detection:
  - Comment in linked group under active thread is recorded.
  - Comment outside active thread is ignored.
- Promo issuing:
  - First eligible attempt returns code.
  - Repeated attempts don’t duplicate issuance (idempotent).
  - Total limit exhaustion returns clear message.

Edge cases
- User without username/first_name/last_name.
- Non-topic group messages (no message_thread_id) are ignored.
- Flood control: rapid messages are throttled (user rate limit message appears once per few seconds).
- Duplicate updates: same message delivered twice is ignored.

Webhook (if enabled)
- Webhook set on startup; 2xx responses returned.
- Requests without correct `X-Telegram-Bot-Api-Secret-Token` rejected (401).
- Reverse proxy path matches `WEBHOOK_URL + WEBHOOK_PATH`.

Observability
- Logs contain structured fields (user_id, post_id) where applicable.
- Errors produce warnings/errors and do not crash the bot.

Data
- DB tables created; comments and promo_issues populated as expected.
- Unique constraints prevent duplicates.

Regression
- Polling fallback still works when webhook is disabled.

Sign-off
- All above scenarios pass on staging with test users.
- README/SETUP and support docs are up to date.
