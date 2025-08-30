from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from ..logging import get_logger
from ..monitoring import setup_monitoring
from .service import (
    fetch_trends,
    get_trending_categories,
    get_design_ideas,
    get_product_suggestions,
)
from .events import EVENTS
from ..tasks import celery_app

app = FastAPI()
_logger = get_logger(__name__)
setup_monitoring(app, "trend_scraper")


@app.on_event("startup")
async def startup_event():
    celery_app.send_task("services.tasks.fetch_trends_task")


@app.get("/trends")
async def get_trends(category: str | None = None):
    return await fetch_trends(category)


class EventsResponse(BaseModel):
    month: str
    events: list[str]


class ProductCategory(BaseModel):
    name: str
    items: list[str]


class DesignIdeaCategory(BaseModel):
    name: str
    ideas: list[str]


class Suggestion(BaseModel):
    category: str
    design_theme: str
    suggestion: str


@app.get("/events/{month}", response_model=EventsResponse)
async def get_events(month: str):
    month_key = month.lower() if month else datetime.utcnow().strftime("%B").lower()
    events = EVENTS.get(month_key, [])
    return {"month": month_key.capitalize(), "events": events}


@app.get("/categories", response_model=list[ProductCategory])
async def get_categories(category: str | None = None):
    return get_trending_categories(category)


@app.get("/design-ideas", response_model=list[DesignIdeaCategory])
async def design_ideas(category: str | None = None):
    return get_design_ideas(category)


@app.get("/suggestions", response_model=list[Suggestion])
async def product_suggestions(category: str | None = None, design: str | None = None):
    return get_product_suggestions(category, design)
