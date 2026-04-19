import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from src.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    description = Column(String, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    status = Column(String, nullable=False, default="pending")
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    webhook_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
