from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    description: str | None = None
    metadata: dict[str, Any] | None = None
    webhook_url: HttpUrl


class PaymentResponse(BaseModel):
    id: UUID
    amount: float
    currency: str
    description: str | None
    metadata: dict[str, Any] | None = Field(None, validation_alias="metadata_")
    status: str
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
