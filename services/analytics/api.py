from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, FastAPI, Query
from pydantic import BaseModel

from ..common.observability import register_observability
from ..models import EventType
from .middleware import AnalyticsMiddleware
from .service import get_summary, get_trending_keywords, list_events, log_event

app = FastAPI()
register_observability(app, service_name="analytics")
app.add_middleware(AnalyticsMiddleware)
router = APIRouter(prefix="/api/analytics")


class KeywordOut(BaseModel):
    term: str
    clicks: int


class EventIn(BaseModel):
    event_type: EventType
    path: str
    user_id: int | None = None
    meta: Dict[str, Any] | None = None


class EventOut(EventIn):
    id: int
    created_at: datetime


class SummaryOut(BaseModel):
    path: str
    views: int
    clicks: int
    conversions: int
    conversion_rate: float


@router.get("", response_model=list[KeywordOut])
async def list_keywords(
    limit: int = Query(default=10, ge=1, le=50),
    lookback_hours: int = Query(default=24 * 7, ge=1, le=24 * 30),
) -> list[KeywordOut]:
    return [
        KeywordOut(**item)
        for item in await get_trending_keywords(limit=limit, lookback_hours=lookback_hours)
    ]


@router.post("/events", response_model=EventOut, status_code=201)
async def create_event(event: EventIn):
    return await log_event(**event.model_dump())


@router.get("/events", response_model=list[EventOut])
async def get_events(event_type: str | None = None):
    events = await list_events(event_type)
    return [EventOut(**e.model_dump()) for e in events]


@router.get("/summary", response_model=list[SummaryOut])
async def summary():
    return await get_summary()


app.include_router(router)
app.add_api_route(
    "/analytics/events",
    create_event,
    methods=["POST"],
    response_model=EventOut,
    status_code=201,
)
app.add_api_route(
    "/analytics/events",
    get_events,
    methods=["GET"],
    response_model=list[EventOut],
)
app.add_api_route(
    "/analytics/summary",
    summary,
    methods=["GET"],
    response_model=list[SummaryOut],
)
