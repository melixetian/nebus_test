from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    webhook_url: HttpUrl


class PaymentResponse(BaseModel):
    id: UUID
    amount: float
    currency: str
    description: Optional[str]
    metadata: Optional[Dict[str, Any]]
    status: str
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True
