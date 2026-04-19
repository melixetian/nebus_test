import asyncio

from fastapi import Depends, FastAPI

from src.api.dependencies import verify_api_key
from src.api.v1.payments import router as payments_router
from src.services.outbox_relay import start_outbox_relay

app = FastAPI(
    title="Async Payment Processing Service",
    description="Microservice for asynchronous payment processing",
    version="1.0.0",
    dependencies=[Depends(verify_api_key)],
)

app.include_router(payments_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    # При старте сервиса запускаем relay для отправки событий в очередь
    asyncio.create_task(start_outbox_relay())
