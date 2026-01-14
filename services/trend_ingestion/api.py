from contextlib import asynccontextmanager
from fastapi import FastAPI
from ..common.observability import register_observability

from .service import get_live_trends, refresh_trends, start_scheduler

@asynccontextmanager
async def _trend_ingestion_lifespan(_: FastAPI):
    start_scheduler()
    yield


app = FastAPI(lifespan=_trend_ingestion_lifespan)
register_observability(app, service_name="trend_ingestion")


@app.get("/trends/live")
async def live_trends(category: str | None = None):
    return await get_live_trends(category)


@app.post("/trends/refresh")
async def refresh_endpoint():
    await refresh_trends()
    return {"status": "ok"}
