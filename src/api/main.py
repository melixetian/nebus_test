import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from src.api.dependencies import verify_api_key
from src.api.v1.payments import router as payments_router
from src.services.outbox_relay import start_outbox_relay


@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте сервиса запускаем relay для отправки событий в очередь
    task = asyncio.create_task(start_outbox_relay())
    yield
    task.cancel()


app = FastAPI(
    title="Async Payment Processing Service",
    description="Microservice for asynchronous payment processing",
    version="1.0.0",
    dependencies=[Depends(verify_api_key)],
    lifespan=lifespan,
)

app.include_router(payments_router, prefix="/api/v1")
