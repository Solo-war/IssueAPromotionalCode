# Обновления и Расширения

1) Персонифицированные промокоды
- Хранение: добавить таблицу `promotions` (code pool) и `promo_codes` (уникальные коды с флагом redeemed).
- Логика: `PromoService` выдаёт персональный код из пула (reserve + mark issued). Идемпотентность по (user_id, promotion_id).
- Интеграции: опционально получать/синхронизировать коды из внешнего CRM или купонного сервиса (API).

2) Интеграция с CRM
- Вебхуки/ETL: отправлять событие `PromoIssued` в CRM (user_id, username, timestamp).
- Сегментации: выгружать пользователей, у кого не получилось (NotSubscribed/NoComment) — ретаргетинг.
- Consent & Privacy: хранить только минимум персональных данных.

3) Улучшение антиспама
- Persistent rate limiting (Redis) вместо in-memory.
- Антибот-эвристики: флаги по скорости, возрасту аккаунта, числу попыток.

4) Отчётность
- Автоматический еженедельный отчёт: запуск скрипта `python scripts/weekly_report.py` по cron/CI, публикация в Slack/Telegram/Email.
- Дашборды: Grafana панели для основных метрик.

5) Масштабирование
- Webhook + HPA в Kubernetes, readiness/liveness пробы.
- Outbox + background worker для надёжной отправки DM (если добавим персональные коды и очереди).
