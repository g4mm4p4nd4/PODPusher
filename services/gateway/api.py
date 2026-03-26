from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from pydantic import BaseModel

from ..ab_tests.api import app as ab_app
from ..analytics.api import router as analytics_router
from ..analytics.middleware import AnalyticsMiddleware
from ..auth.api import app as auth_app
from ..billing.api import app as billing_app
from ..bulk_create.api import BulkCreateResponse, bulk_create as bulk_create_handler
from ..common.auth import require_user_id
from ..common.cache import CACHE_TTL_TRENDS, cache_get, cache_key, cache_set
from ..common.errors import register_error_handlers
from ..common.observability import register_observability
from ..common.product_pipeline import assemble_products
from ..common.quotas import check_quota, increment_quota, quota_exceeded_response
from ..common.rate_limit import register_rate_limiting
from ..ideation.api import app as ideation_app
from ..ideation.service import generate_ideas
from ..image_gen.service import delete_image, generate_image_for_idea, generate_images, list_images
from ..integration.service import create_sku, load_oauth_credentials, publish_listing
from ..listing_composer.api import app as listing_app
from ..models import OAuthProvider
from ..notifications.api import app as notifications_app
from ..product.api import app as product_app
from ..search.api import app as search_app
from ..social_generator.api import app as social_app
from ..trend_ingestion.service import get_live_trends, get_refresh_status, refresh_trends, start_scheduler
from ..trend_scraper.events import EVENTS
from ..trend_scraper.service import fetch_trends, get_design_ideas, get_product_suggestions, get_trending_categories
from ..user.api import router as user_router


@asynccontextmanager
async def _gateway_lifespan(_: FastAPI):
    start_scheduler()
    yield


class ImageGenerateRequest(BaseModel):
    idea_id: int
    style: str = "default"
    provider_override: str | None = None


app = FastAPI(lifespan=_gateway_lifespan)
register_observability(app, service_name="gateway")
register_error_handlers(app)
register_rate_limiting(app)
app.include_router(analytics_router)
app.include_router(user_router)
app.mount("/api/products", product_app)
app.mount("/api/notifications", notifications_app)
app.mount("/api/search", search_app)
app.mount("/ab_tests", ab_app)
app.mount("/api/ideation", ideation_app)
app.mount("/api/listing-composer", listing_app)
app.mount("/api/social", social_app)
app.mount("/api/auth", auth_app)
app.mount("/api/billing", billing_app)
app.add_middleware(AnalyticsMiddleware)


@app.post("/generate")
async def generate(
    category: str | None = None,
    user_id: int = Depends(require_user_id),
):
    trends = await fetch_trends(category)
    if not trends:
        raise HTTPException(status_code=503, detail="No trends available")
    ideas = await generate_ideas(trends)
    if not ideas:
        raise HTTPException(status_code=503, detail="Failed to generate ideas")
    images = await generate_images(ideas)
    if not images:
        raise HTTPException(status_code=503, detail="Failed to generate product images")
    product_inputs = assemble_products(ideas, images)
    if not product_inputs:
        raise HTTPException(status_code=503, detail="Unable to build product payloads")

    printify_credentials = await load_oauth_credentials(user_id, OAuthProvider.PRINTIFY)
    etsy_credentials = await load_oauth_credentials(user_id, OAuthProvider.ETSY)

    missing_providers: list[str] = []
    if not printify_credentials:
        missing_providers.append(OAuthProvider.PRINTIFY.value)
    if not etsy_credentials:
        missing_providers.append(OAuthProvider.ETSY.value)

    products_payload = [dict(product) for product in product_inputs]
    listing: dict | None = None
    listing_url: str | None = None

    if not missing_providers:
        products = create_sku(product_inputs, credential=printify_credentials)
        if not products:
            raise HTTPException(status_code=502, detail="Printify did not return any products")
        products_payload = [dict(product) for product in products]
        listing = publish_listing(dict(products[0]), credential=etsy_credentials)
        if not listing:
            raise HTTPException(status_code=502, detail="Unable to publish listing")
        listing_url = listing.get("etsy_url")
        if listing_url:
            listing["listing_url"] = listing_url

    month = datetime.utcnow().strftime("%B").lower()
    events = EVENTS.get(month, [])

    response = {
        "listing_url": listing_url,
        "listing": listing,
        "events": events,
        "products": products_payload,
        "ideas": ideas,
        "trends": trends,
        "auth": {
            "user_id": user_id,
            "printify_linked": bool(printify_credentials),
            "etsy_linked": bool(etsy_credentials),
            "missing": missing_providers,
        },
    }
    return response


@app.post("/api/images/generate")
async def generate_image_endpoint(
    payload: ImageGenerateRequest,
    user_id: int = Depends(require_user_id),
):
    allowed, details = await check_quota(user_id, "images", 1)
    if not allowed:
        return quota_exceeded_response(details)

    images = await generate_image_for_idea(
        idea_id=payload.idea_id,
        style=payload.style,
        provider_override=payload.provider_override,
    )
    if not images:
        raise HTTPException(status_code=404, detail="Idea not found")

    await increment_quota(user_id, "images", 1)
    return images


@app.get("/api/images")
async def list_images_endpoint(
    idea_id: int,
    _user_id: int = Depends(require_user_id),
):
    return await list_images(idea_id)


@app.delete("/api/images/{image_id}")
async def delete_image_endpoint(
    image_id: int,
    _user_id: int = Depends(require_user_id),
):
    deleted = await delete_image(image_id)
    if deleted["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Image not found")
    return deleted


@app.post("/api/bulk_create", response_model=BulkCreateResponse)
async def bulk_create(request: Request):
    return await bulk_create_handler(request)


@app.get("/trends")
async def list_trends(category: str | None = None):
    ck = cache_key("trends", category or "all")
    cached = cache_get(ck)
    if cached is not None:
        return cached
    result = await fetch_trends(category)
    cache_set(ck, result, CACHE_TTL_TRENDS)
    return result


@app.get("/events/{month}")
async def list_events(month: str):
    month_key = (month or datetime.utcnow().strftime("%B")).lower()
    events = EVENTS.get(month_key, [])
    return {"month": month_key.capitalize(), "events": events}


@app.get("/product-categories")
async def product_categories(category: str | None = None):
    return get_trending_categories(category)


@app.get("/design-ideas")
async def design_ideas(category: str | None = None):
    return get_design_ideas(category)


@app.get("/product-suggestions")
async def product_suggestions(category: str | None = None, design: str | None = None):
    return get_product_suggestions(category, design)


@app.get("/api/trends/live")
async def live_trends(
    category: str | None = None,
    source: str | None = None,
    lookback_hours: int = Query(default=72, ge=1, le=24 * 14),
    limit: int = Query(default=5, ge=1, le=50),
):
    ck = cache_key("live_trends", category or "all", source or "all", str(lookback_hours), str(limit))
    cached = cache_get(ck)
    if cached is not None:
        return cached
    result = await get_live_trends(
        category=category,
        source=source,
        lookback_hours=lookback_hours,
        per_group_limit=limit,
    )
    cache_set(ck, result, CACHE_TTL_TRENDS)
    return result


@app.get("/api/trends/live/status")
async def live_trends_status():
    return get_refresh_status()


@app.post("/api/trends/refresh")
async def refresh_trends_endpoint():
    return await refresh_trends()
