from fastapi import FastAPI

from services.trend_scraper.main import fetch_trends
from services.ideation.main import generate_ideas
from services.image_gen.main import generate_images
from services.integration.main import create_sku, publish_listing

app = FastAPI()


@app.post("/generate")
async def generate() -> dict:
    """Orchestrate the stub pipeline."""
    trends = fetch_trends()
    ideas = generate_ideas(trends)
    images = generate_images(ideas[0])
    product = create_sku(ideas[0])
    listing = publish_listing(product)
    return {
        "trends": trends,
        "ideas": ideas,
        "images": images,
        "product": product,
        "listing": listing.get("listing_url"),
    }
