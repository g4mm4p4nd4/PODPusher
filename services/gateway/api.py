from datetime import datetime
from fastapi import FastAPI
from ..trend_scraper.service import fetch_trends, get_trending_categories
from ..ideation.service import generate_ideas
from ..image_gen.service import generate_images
from ..integration.service import create_sku, publish_listing
from ..trend_scraper.events import EVENTS

app = FastAPI()


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
