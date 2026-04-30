import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..ab_tests.api import app as ab_app
from ..analytics.api import router as analytics_router
from ..analytics.middleware import AnalyticsMiddleware
from ..auth.api import app as auth_app
from ..billing.api import app as billing_app
from ..billing.service import STUB_MODE as BILLING_STUB_MODE
from ..bulk_create.api import BulkCreateResponse, bulk_create as bulk_create_handler
from ..common.auth import require_user_id
from ..common.cache import CACHE_TTL_TRENDS, cache_clear, cache_get, cache_key, cache_set
from ..common.errors import register_error_handlers
from ..common.observability import register_observability
from ..common.product_pipeline import assemble_products
from ..common.quotas import check_quota, increment_quota, quota_exceeded_response
from ..common.rate_limit import register_rate_limiting
from ..common.time import utcnow
from ..control_center.service import get_trend_insights
from ..dashboard.api import app as dashboard_app
from ..ideation.api import app as ideation_app
from ..ideation.service import generate_ideas
from ..image_gen.service import (
    delete_image,
    generate_image_for_idea,
    generate_images,
    list_images,
)
from ..integration.service import create_sku, load_oauth_credentials, publish_listing
from ..listing_composer.api import app as listing_app
from ..models import OAuthProvider
from ..niches.api import app as niches_app
from ..notifications.api import app as notifications_app
from ..product.api import app as product_app
from ..search.api import app as search_app
from ..seasonal.api import app as seasonal_app
from ..settings.api import app as settings_app
from ..social_generator.api import app as social_app
from ..trend_ingestion.service import (
    get_live_trends,
    get_refresh_status,
    refresh_trends,
    start_scheduler,
)
from ..trend_scraper.events import EVENTS
from ..trend_scraper.service import (
    fetch_trends,
    get_design_ideas,
    get_product_suggestions,
    get_trending_categories,
)
from ..user.api import router as user_router
from packages.integrations import openai as openai_integration


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
_allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://frontend:3000,http://localhost:3002,http://127.0.0.1:3002",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(analytics_router)
app.include_router(user_router)
app.mount("/api/products", product_app)
app.mount("/api/notifications", notifications_app)
app.mount("/api/search", search_app)
app.mount("/api/dashboard", dashboard_app)
app.mount("/api/seasonal", seasonal_app)
app.mount("/api/niches", niches_app)
app.mount("/api/settings", settings_app)
app.mount("/ab_tests", ab_app)
app.mount("/api/ab-tests", ab_app)
app.mount("/api/ideation", ideation_app)
app.mount("/api/listing-composer", listing_app)
app.mount("/api/social", social_app)
app.mount("/api/auth", auth_app)
app.mount("/api/billing", billing_app)
app.add_middleware(AnalyticsMiddleware)


def _capability(
    *,
    configured: bool,
    live_label: str,
    missing_label: str,
    required: list[str],
) -> dict[str, object]:
    return {
        "status": "live" if configured else "needs_implementation",
        "configured": configured,
        "blocking": not configured,
        "message": live_label if configured else missing_label,
        "required": required if not configured else [],
    }


@app.get("/api/system/capabilities")
async def system_capabilities():
    """Expose production-readiness status for credential-backed features."""
    trend_stub_enabled = os.getenv("TREND_INGESTION_STUB") == "1"
    printify_configured = bool(
        os.getenv("PRINTIFY_API_KEY") and os.getenv("PRINTIFY_SHOP_ID")
    )
    etsy_configured = bool(
        os.getenv("ETSY_CLIENT_ID")
        and os.getenv("ETSY_ACCESS_TOKEN")
        and os.getenv("ETSY_SHOP_ID")
    )
    return {
        "overall_status": "needs_implementation",
        "generated_at": utcnow().isoformat(),
        "capabilities": {
            "trend_refresh": {
                "status": "stub" if trend_stub_enabled else "live_public_only",
                "configured": not trend_stub_enabled,
                "blocking": False,
                "message": "Public-only trend ingestion is available; blocked sources are reported in live status.",
                "required": [],
            },
            "openai_ideation": _capability(
                configured=bool(openai_integration.API_KEY and not openai_integration.USE_STUB),
                live_label="OpenAI ideation is configured.",
                missing_label="OpenAI ideation/image generation is not configured; generated AI output will be marked needs_implementation.",
                required=["OPENAI_API_KEY", "OPENAI_USE_STUB=0"],
            ),
            "printify_product_creation": _capability(
                configured=printify_configured,
                live_label="Printify product creation is configured.",
                missing_label="Printify product creation is not configured; publish flows remain local only.",
                required=["PRINTIFY_API_KEY", "PRINTIFY_SHOP_ID"],
            ),
            "etsy_listing_publish": _capability(
                configured=etsy_configured,
                live_label="Etsy listing publishing is configured.",
                missing_label="Etsy listing publishing is not configured; publish flows remain local only.",
                required=["ETSY_CLIENT_ID", "ETSY_ACCESS_TOKEN", "ETSY_SHOP_ID"],
            ),
            "stripe_billing": _capability(
                configured=not BILLING_STUB_MODE,
                live_label="Stripe billing is configured.",
                missing_label="Stripe billing is not configured; billing portal and subscription data are unavailable.",
                required=["STRIPE_SECRET_KEY", "BILLING_STUB_MODE=false"],
            ),
        },
    }


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
            raise HTTPException(
                status_code=502, detail="Printify did not return any products"
            )
        products_payload = [dict(product) for product in products]
        listing = publish_listing(dict(products[0]), credential=etsy_credentials)
        if not listing:
            raise HTTPException(status_code=502, detail="Unable to publish listing")
        listing_url = listing.get("etsy_url")
        if listing_url:
            listing["listing_url"] = listing_url

    month = utcnow().strftime("%B").lower()
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
    month_key = (month or utcnow().strftime("%B")).lower()
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
    page: int = Query(default=1, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=50),
    sort_by: str = Query(default="engagement_score", pattern="^(engagement_score|timestamp|keyword)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    include_meta: bool = False,
):
    ck = cache_key(
        "live_trends",
        category or "all",
        source or "all",
        str(lookback_hours),
        str(limit),
        str(page),
        str(page_size or ""),
        sort_by,
        sort_order,
        str(include_meta),
    )
    cached = cache_get(ck)
    if cached is not None:
        return cached
    result = await get_live_trends(
        category=category,
        source=source,
        lookback_hours=lookback_hours,
        per_group_limit=limit,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        include_meta=include_meta,
    )
    cache_set(ck, result, CACHE_TTL_TRENDS)
    return result


@app.get("/api/trends/live/status")
async def live_trends_status():
    return get_refresh_status()


@app.post("/api/trends/refresh")
async def refresh_trends_endpoint():
    result = await refresh_trends()
    cache_clear()
    return result


@app.get("/api/trends/insights")
async def trend_insights(
    marketplace: str = "etsy",
    category: str | None = None,
    country: str = "US",
    language: str = "en",
    lookback_days: int = Query(default=30, ge=1, le=180),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    sort_by: str = Query(default="search_volume", pattern="^(search_volume|growth|competition|keyword|opportunity)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    return await get_trend_insights(
        marketplace=marketplace,
        category=category,
        country=country,
        language=language,
        lookback_days=lookback_days,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
