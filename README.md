# Async Payment Processing Service

Асинхронный микросервис для обработки платежей.

## Технологии

- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (async) + Alembic
- PostgreSQL
- RabbitMQ + FastStream
- Docker + docker-compose

## Архитектура

Сервис состоит из следующих компонентов:
1. **API**: Принимает запросы на создание платежей, сохраняет их в БД и записывает событие в таблицу `outbox` (Outbox Pattern).
2. **Outbox Relay**: Фоновая задача в API-сервисе, которая читает новые события из таблицы `outbox` и гарантированно отправляет их в RabbitMQ.
3. **Consumer**: Воркер на базе FastStream, который читает сообщения из RabbitMQ, эмулирует обработку платежа, обновляет статус в БД и отправляет webhook. Реализована идемпотентность и механизм retry.
4. **DLQ (Dead Letter Queue)**: Очередь для сообщений, которые не удалось обработать после 3 попыток.

## Запуск проекта

1. Скопируйте `.env.example` в `.env` и заполните переменные окружения:
```bash
cp .env.example .env
```

2. Запустите проект через Makefile:
```bash
make run
```
Эта команда соберет образы и запустит все 4 контейнера (`postgres`, `rabbitmq`, `api`, `consumer`). Миграции БД применятся автоматически при старте `api`.

3. Для остановки проекта:
```bash
make down
```

4. Просмотр логов:
```bash
make logs
```

## Тестирование

Для проверки работы API и Consumer'а написан bash-скрипт, который отправляет запросы к локально запущенному сервису и проверяет ответы.

Запустить тесты (убедитесь, что сервисы запущены через `make run`):
```bash
make test
```

## Примеры запросов (API)

API защищено статическим ключом `X-API-Key` (по умолчанию `secret_api_key`).

### Создание платежа

```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "X-API-Key: secret_api_key" \
  -H "Idempotency-Key: my-unique-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100.50,
    "currency": "RUB",
    "description": "Test payment",
    "metadata": {"user_id": 1},
    "webhook_url": "https://webhook.site/your-webhook-url"
  }'
```
*Ответ: `202 Accepted`*

### Получение информации о платеже

```bash
curl -X GET http://localhost:8000/api/v1/payments/{payment_id} \
  -H "X-API-Key: secret_api_key"
```
