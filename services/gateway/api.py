from datetime import datetime
import csv
import json
from typing import Dict, List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from pydantic import BaseModel, HttpUrl, ValidationError, Field

from ..logging import get_logger
from ..monitoring import setup_monitoring
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
from ..listing_composer.api import app as listing_app
from ..social_generator.api import app as social_app
from ..trend_scraper.events import EVENTS
from ..analytics.middleware import AnalyticsMiddleware

app = FastAPI()
logger = get_logger(__name__)
setup_monitoring(app)
app.mount("/api/images/review", review_app)
app.mount("/api/notifications", notifications_app)
app.mount("/api/search", search_app)
app.mount("/ab_tests", ab_app)
app.mount("/api/ideation", ideation_app)
app.mount("/api/listing-composer", listing_app)
app.mount("/api/social", social_app)
app.add_middleware(AnalyticsMiddleware)


class Variant(BaseModel):
    sku: Optional[str] = None
    price: float = Field(..., gt=0)
    options: Dict[str, str] | None = None


class ProductDefinition(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    variants: List[Variant] = []
    image_urls: List[HttpUrl] = []


class BulkResult(BaseModel):
    created: int
    errors: List[str]


@app.post("/api/bulk_create", response_model=BulkResult)
async def bulk_create(request: Request, file: UploadFile | None = File(None)):
    items: List[Dict] = []
    if request.headers.get("content-type", "").startswith("application/json"):
        body = await request.json()
        items = body.get("products", [])
    elif file is not None:
        content = await file.read()
        try:
            if file.filename.endswith(".json"):
                items = json.loads(content)
            else:
                reader = csv.DictReader(content.decode().splitlines())
                for row in reader:
                    if row.get("image_urls"):
                        row["image_urls"] = [u.strip() for u in row["image_urls"].split(",") if u.strip()]
                    items.append(row)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid file")
    else:
        raise HTTPException(status_code=400, detail="No input provided")

    created = 0
    errors: List[str] = []
    for idx, item in enumerate(items):
        try:
            prod = ProductDefinition(**item)
            create_sku([prod.dict()])
            created += 1
        except ValidationError as exc:
            errors.append(f"{idx}: {exc.errors()}")
        except Exception as exc:  # pragma: no cover - unexpected errors
            errors.append(f"{idx}: {str(exc)}")
    return {"created": created, "errors": errors}


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
