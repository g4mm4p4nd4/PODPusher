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
from ..image_gen.service import generate_images
from ..integration.service import create_sku, publish_listing
from ..image_review.api import app as review_app
from ..notifications.api import app as notifications_app
from ..search.api import app as search_app
from ..ab_tests.api import app as ab_app
from ..trend_scraper.events import EVENTS
from ..analytics.middleware import AnalyticsMiddleware

app = FastAPI()
app.mount("/api/images/review", review_app)
app.mount("/api/notifications", notifications_app)
app.mount("/api/search", search_app)
app.mount("/ab_tests", ab_app)
app.mount("/api/ideation", ideation_app)
app.add_middleware(AnalyticsMiddleware)


@app.post("/generate")
async def generate():
    trends = await fetch_trends()
    ideas = await generate_ideas(trends)
    images = await generate_images([i["description"] for i in ideas])
    products = create_sku(images)
    listing = publish_listing(products[0])
    month = datetime.utcnow().strftime("%B").lower()
    events = EVENTS.get(month, [])
    listing["listing_url"] = listing.get("etsy_url")
    listing["events"] = events
    return listing


@app.get("/product-categories")
async def product_categories(category: str | None = None):
    return get_trending_categories(category)


@app.get("/design-ideas")
async def design_ideas(category: str | None = None):
    return get_design_ideas(category)


@app.get("/product-suggestions")
async def product_suggestions(category: str | None = None, design: str | None = None):
    return get_product_suggestions(category, design)
