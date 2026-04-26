from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query

from ..common.auth import require_user_id
from ..common.observability import register_observability
from .circuit_breaker import scraper_circuit_breaker
from .service import get_live_trends, get_refresh_status, refresh_trends, start_scheduler


@asynccontextmanager
async def _trend_ingestion_lifespan(_: FastAPI):
    start_scheduler()
    yield


app = FastAPI(lifespan=_trend_ingestion_lifespan)
register_observability(app, service_name="trend_ingestion")


@app.get("/trends/live")
async def live_trends(
    category: str | None = None,
    source: str | None = None,
    lookback_hours: int = Query(default=72, ge=1, le=24 * 14),
    limit: int = Query(default=5, ge=1, le=50),
    page: int = Query(default=1, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=50),
    sort_by: str = Query(default="engagement_score", pattern="^(engagement_score|timestamp|keyword)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    include_meta: bool = False,
):
    return await get_live_trends(
        category=category,
        source=source,
        lookback_hours=lookback_hours,
        per_group_limit=limit,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        include_meta=include_meta,
    )


@app.get("/trends/live/status")
async def live_trends_status():
    return get_refresh_status()


@app.post("/trends/refresh")
async def refresh_endpoint(_: int = Depends(require_user_id)):
    return await refresh_trends()


@app.get("/trends/scraper-status")
async def scraper_status():
    from .sources import PLATFORM_CONFIG

    return {name: scraper_circuit_breaker.state(name).value for name in PLATFORM_CONFIG}
