import asyncio
import logging

from faststream.rabbit import RabbitBroker
from sqlalchemy.future import select

from src.core.config import settings
from src.db.session import AsyncSessionLocal
from src.models.outbox import OutboxEvent

logger = logging.getLogger(__name__)


async def start_outbox_relay():
    """Запустить relay для отправки событий в очередь."""
    broker = RabbitBroker(settings.RABBITMQ_URL)
    await broker.connect()

    try:
        while True:
            try:
                async with AsyncSessionLocal() as session:
                    async with session.begin():
                        # Fetch pending events
                        stmt = (
                            select(OutboxEvent)
                            .where(OutboxEvent.status == "pending")
                            .limit(100)
                            .with_for_update(skip_locked=True)
                        )
                        result = await session.execute(stmt)
                        events = result.scalars().all()

                        for event in events:
                            # Publish to RabbitMQ
                            await broker.publish(event.payload, queue="payments.new")
                            # Mark as processed
                            event.status = "processed"
                            session.add(event)
            except Exception as exc:
                logger.error(f"Error in outbox relay: {exc}")

            await asyncio.sleep(1)
    finally:
        await broker.close()
