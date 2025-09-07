from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
from .service import log_event, list_events, get_summary
from ..models import EventType
from .middleware import AnalyticsMiddleware
from ..common.monitoring import setup_observability

app = FastAPI()
setup_observability(app)
app.add_middleware(AnalyticsMiddleware)


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


@app.post("/analytics/events", response_model=EventOut, status_code=201)
async def create_event(event: EventIn):
    return await log_event(**event.model_dump())


@app.get("/analytics/events", response_model=list[EventOut])
async def get_events(event_type: str | None = None):
    events = await list_events(event_type)
    return [EventOut(**e.model_dump()) for e in events]


@app.get("/analytics/summary", response_model=list[SummaryOut])
async def summary():
    return await get_summary()
