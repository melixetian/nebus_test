from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.db.session import get_db
from src.models.outbox import OutboxEvent
from src.models.payment import Payment
from src.schemas.payment import PaymentCreate, PaymentResponse

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_payment(
    payment_in: PaymentCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
):
    """Создать платеж."""
    try:
        async with db.begin():
            payment = Payment(
                amount=payment_in.amount,
                currency=payment_in.currency,
                description=payment_in.description,
                metadata_=payment_in.metadata,
                idempotency_key=idempotency_key,
                webhook_url=str(payment_in.webhook_url),
                status="pending",
            )
            db.add(payment)

            # Flush to get payment.id and trigger IntegrityError if idempotency_key exists
            await db.flush()

            payload = {
                "payment_id": str(payment.id),
                "amount": float(payment.amount),
                "currency": payment.currency,
                "description": payment.description,
                "metadata": payment.metadata_,
                "webhook_url": payment.webhook_url,
            }
            outbox_event = OutboxEvent(payload=payload, status="pending")
            db.add(outbox_event)

        return payment
    except IntegrityError:
        # Transaction is rolled back automatically by db.begin()
        stmt = select(Payment).where(Payment.idempotency_key == idempotency_key)
        result = await db.execute(stmt)
        existing_payment = result.scalar_one_or_none()
        if existing_payment:
            return existing_payment
        raise HTTPException(status_code=500, detail="Database integrity error")


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Получить платеж по ID."""
    stmt = select(Payment).where(Payment.id == payment_id)
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment
