from datetime import datetime
from fastapi import FastAPI
from ..trend_scraper.service import (
    fetch_trends,
    get_trending_categories,
    get_design_ideas,
    get_product_suggestions,
)
from ..ideation.service import generate_ideas
from ..ideation.api import app as ideation_app
from ..image_gen.service import generate_images, list_images, delete_image
from ..integration.service import create_sku, publish_listing
from ..image_review.api import app as review_app
from ..notifications.api import app as notifications_app
from ..search.api import app as search_app
from ..ab_tests.api import app as ab_app
from ..listing_composer.api import app as listing_app
from ..social_generator.api import app as social_app
from ..bulk_create.api import BulkCreateResponse, bulk_create as bulk_create_handler
from fastapi import Request
from ..trend_scraper.events import EVENTS
from ..analytics.middleware import AnalyticsMiddleware
from ..common.database import get_session
from ..models import Idea
from sqlmodel import select
from pydantic import BaseModel

app = FastAPI()
app.mount("/api/images/review", review_app)
app.mount("/api/notifications", notifications_app)
app.mount("/api/search", search_app)
app.mount("/ab_tests", ab_app)
app.mount("/api/ideation", ideation_app)
app.mount("/api/listing-composer", listing_app)
app.mount("/api/social", social_app)
app.add_middleware(AnalyticsMiddleware)


class ImageRequest(BaseModel):
    idea_id: int
    style: str
    provider_override: str | None = None


@app.post("/api/images/generate")
async def generate_image_endpoint(data: ImageRequest):
    return await generate_images(data.idea_id, data.style, data.provider_override)


@app.get("/api/images")
async def list_images_endpoint(idea_id: int):
    return await list_images(idea_id)


@app.delete("/api/images/{image_id}")
async def delete_image_endpoint(image_id: int):
    return await delete_image(image_id)

@app.post("/generate")
async def generate():
    trends = await fetch_trends()
    await generate_ideas(trends)
    async with get_session() as session:
        result = await session.exec(select(Idea))
        idea_ids = [i.id for i in result.all()]
    image_urls = []
    for iid in idea_ids:
        image_urls.extend(await generate_images(iid, "default"))
    products = create_sku([{"image_url": u} for u in image_urls])
    listing = publish_listing(products[0])
    month = datetime.utcnow().strftime("%B").lower()
    events = EVENTS.get(month, [])
    listing["listing_url"] = listing.get("etsy_url")
    listing["events"] = events
    return listing


@app.post("/api/bulk_create", response_model=BulkCreateResponse)
async def bulk_create(request: Request):
    return await bulk_create_handler(request)


@app.get("/product-categories")
async def product_categories(category: str | None = None):
    return get_trending_categories(category)


@app.get("/design-ideas")
async def design_ideas(category: str | None = None):
    return get_design_ideas(category)


@app.get("/product-suggestions")
async def product_suggestions(category: str | None = None, design: str | None = None):
    return get_product_suggestions(category, design)
