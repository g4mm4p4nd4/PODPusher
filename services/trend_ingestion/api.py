from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from ..common.auth import require_user_id
from ..common.observability import register_observability

from .circuit_breaker import scraper_circuit_breaker
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
async def refresh_endpoint(user_id: int = Depends(require_user_id)):
    """Trigger an immediate trend refresh. Requires authentication."""
    await refresh_trends()
    return {"status": "ok"}


@app.get("/trends/scraper-status")
async def scraper_status():
    """Return circuit breaker state for each platform."""
    from .sources import PLATFORM_CONFIG
    return {
        name: scraper_circuit_breaker.state(name).value
        for name in PLATFORM_CONFIG
    }
