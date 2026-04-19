import asyncio
import random
from datetime import datetime

import httpx
from faststream import FastStream, Logger
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue
from sqlalchemy.future import select

from src.core.config import settings
from src.db.session import AsyncSessionLocal
from src.models.payment import Payment

broker = RabbitBroker(settings.RABBITMQ_URL)
app = FastStream(broker)

dlq_exchange = RabbitExchange("dlq_exchange")
dlq_queue = RabbitQueue("payments.dlq", routing_key="payments.dlq")

main_queue = RabbitQueue(
    "payments.new",
    arguments={
        "x-dead-letter-exchange": "dlq_exchange",
        "x-dead-letter-routing-key": "payments.dlq",
    },
)


@broker.subscriber(main_queue)
async def process_payment(msg: dict, logger: Logger):
    """Обработать платеж из очереди."""
    payment_id = msg.get("payment_id")
    # webhook_url = msg.get("webhook_url")

    logger.info(f"Processing payment {payment_id}")

    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = select(Payment).where(Payment.id == payment_id).with_for_update()
            result = await session.execute(stmt)
            payment = result.scalar_one_or_none()

            if not payment:
                logger.error(f"Payment {payment_id} not found")
                return

            if payment.status in ["succeeded", "failed"]:
                logger.info(f"Payment {payment_id} already processed with status {payment.status}")
                # Skip processing, just send webhook
                await send_webhook(payment, logger)
                return

            # Emulate processing (2-5 seconds)
            await asyncio.sleep(random.uniform(2.0, 5.0))

            # 90% success, 10% failure
            if random.random() < 0.9:
                payment.status = "succeeded"
            else:
                payment.status = "failed"

            payment.processed_at = datetime.utcnow()
            session.add(payment)

        # Send webhook outside of transaction
        await send_webhook(payment, logger)


async def send_webhook(payment: Payment, logger: Logger):
    """Отправить webhook для платежа."""
    payload = {"payment_id": str(payment.id), "status": payment.status, "metadata": payment.metadata_}

    async with httpx.AsyncClient() as client:
        for attempt in range(3):
            try:
                response = await client.post(payment.webhook_url, json=payload, timeout=10.0)
                response.raise_for_status()
                logger.info(f"Webhook sent for payment {payment.id}")
                return
            except httpx.HTTPError as exc:
                if attempt == 2:
                    logger.error(f"Failed to send webhook for payment {payment.id}: {exc}")
                    # Поднимаем исключение для перемещения в DLQ
                    raise exc

                # Увеличиваем задержку между попытками экспоненциально
                delay = 2.0 * (2**attempt)
                logger.warning(f"Webhook failed for payment {payment.id}, retrying in {delay}s... ({attempt + 1}/3)")
                await asyncio.sleep(delay)
