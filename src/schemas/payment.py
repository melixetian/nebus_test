from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    currency: Literal["RUB", "USD", "EUR"] = Field(...)
    description: str | None = None
    metadata: dict[str, Any] | None = None
    webhook_url: HttpUrl


class PaymentResponse(BaseModel):
    id: UUID
    amount: Decimal
    currency: Literal["RUB", "USD", "EUR"]
    description: str | None
    metadata: dict[str, Any] | None = Field(None, validation_alias="metadata_")
    status: Literal["pending", "succeeded", "failed"]
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
