import os

import pytest

from services.common.database import init_db
from services.ideation.service import generate_ideas
from services.image_gen.service import generate_images
from services.integration.service import create_sku, publish_listing
from services.trend_scraper.service import fetch_trends

_TRUE_VALUES = {"1", "true", "yes", "on"}
_REQUIRED_ENV = (
    "OPENAI_API_KEY",
    "ETSY_CLIENT_ID",
    "ETSY_ACCESS_TOKEN",
    "ETSY_SHOP_ID",
    "PRINTIFY_API_KEY",
    "PRINTIFY_SHOP_ID",
)


def _staging_enabled() -> bool:
    return os.getenv("POD_STAGING_SMOKE", "").strip().lower() in _TRUE_VALUES


def _missing_required_env() -> list[str]:
    return [name for name in _REQUIRED_ENV if not os.getenv(name)]


@pytest.mark.asyncio
async def test_staging_trend_to_listing_smoke():
    if not _staging_enabled():
        pytest.skip("Set POD_STAGING_SMOKE=1 to run credential-backed staging smoke")

    missing = _missing_required_env()
    if missing:
        pytest.fail(f"Missing required staging credentials: {', '.join(missing)}")

    os.environ["OPENAI_USE_STUB"] = "0"
    category = os.getenv("POD_STAGING_CATEGORY", "general")

    await init_db()

    trends = await fetch_trends(category=category)
    assert trends, "No trends returned from trend stage"

    ideas = await generate_ideas(trends[:1])
    assert ideas, "No ideas returned from ideation stage"

    images = await generate_images(ideas[:1])
    assert images and images[0].get("image_url"), "No images returned from image stage"

    products = create_sku(images[:1])
    assert products and products[0].get("sku"), "No SKU returned from Printify stage"
    assert not str(products[0]["sku"]).startswith("stub-"), "Printify call fell back to stub"

    listing = publish_listing(products[0])
    assert listing.get("listing_id"), "No listing ID returned from Etsy stage"
    assert not str(listing["listing_id"]).startswith("stub"), "Etsy call fell back to stub"
