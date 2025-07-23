from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from .service import fetch_trends
from .events import EVENTS
from ..tasks import celery_app

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    celery_app.send_task("services.tasks.fetch_trends_task")


@app.get("/trends")
async def get_trends(category: str | None = None):
    return await fetch_trends(category)


class EventsResponse(BaseModel):
    month: str
    events: list[str]


@app.get("/events/{month}", response_model=EventsResponse)
async def get_events(month: str):
    month_key = month.lower() if month else datetime.utcnow().strftime("%B").lower()
    events = EVENTS.get(month_key, [])
    return {"month": month_key.capitalize(), "events": events}
