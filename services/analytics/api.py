from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
from .service import log_event, list_events, get_summary
from .middleware import AnalyticsMiddleware

app = FastAPI()
app.add_middleware(AnalyticsMiddleware)


class EventIn(BaseModel):
    event_type: str
    path: str
    user_id: int | None = None
    meta: Dict[str, Any] | None = None


class EventOut(EventIn):
    id: int
    created_at: datetime


class SummaryOut(BaseModel):
    path: str
    count: int


@app.post("/analytics/events", response_model=EventOut, status_code=201)
async def create_event(event: EventIn):
    return await log_event(**event.model_dump())


@app.get("/analytics/events", response_model=list[EventOut])
async def get_events(event_type: str | None = None):
    events = await list_events(event_type)
    return [EventOut(**e.model_dump()) for e in events]


@app.get("/analytics/summary", response_model=list[SummaryOut])
async def summary(event_type: str | None = None):
    return await get_summary(event_type)
