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
_STUB_TOGGLES = ("OPENAI_USE_STUB",)


def _staging_enabled() -> bool:
    return os.getenv("POD_STAGING_SMOKE", "").strip().lower() in _TRUE_VALUES


def _missing_required_env() -> list[str]:
    return [name for name in _REQUIRED_ENV if not os.getenv(name)]


def _enabled_stub_toggles() -> list[str]:
    enabled: list[str] = []
    for name in _STUB_TOGGLES:
        value = os.getenv(name, "").strip().lower()
        if value in _TRUE_VALUES:
            enabled.append(name)
    return enabled


def _build_staging_credentials() -> tuple[dict[str, str], dict[str, str]]:
    printify_credential = {
        "access_token": os.environ["PRINTIFY_API_KEY"],
        "account_id": os.environ["PRINTIFY_SHOP_ID"],
    }
    etsy_credential = {
        "access_token": os.environ["ETSY_ACCESS_TOKEN"],
        "account_id": os.environ["ETSY_SHOP_ID"],
    }
    return printify_credential, etsy_credential


@pytest.mark.asyncio
async def test_staging_trend_to_listing_smoke():
    if not _staging_enabled():
        pytest.skip("Set POD_STAGING_SMOKE=1 to run credential-backed staging smoke")

    missing = _missing_required_env()
    if missing:
        pytest.fail(f"Missing required staging credentials: {', '.join(missing)}")

    enabled_stub_toggles = _enabled_stub_toggles()
    if enabled_stub_toggles:
        pytest.fail(
            "Disable stub toggles for live staging smoke: "
            + ", ".join(enabled_stub_toggles)
        )

    category = os.getenv("POD_STAGING_CATEGORY", "general")

    await init_db()

    trends = await fetch_trends(category=category)
    assert trends, "No trends returned from trend stage"
    assert all(
        item.get("trend_source") == "live" for item in trends
    ), "Trend stage returned fallback data (expected live trends)"

    ideas = await generate_ideas(trends[:1])
    assert ideas, "No ideas returned from ideation stage"
    assert all(
        item.get("generation_source") == "openai" for item in ideas
    ), "Ideation stage did not return live OpenAI output"

    images = await generate_images(ideas[:1])
    assert images and images[0].get("image_url"), "No images returned from image stage"
    assert all(
        item.get("generation_source") == "openai" for item in images
    ), "Image stage did not return live OpenAI output"
    assert all(
        item.get("image_url") != "http://example.com/image.png" for item in images
    ), "Image stage returned stub image URLs"

    printify_credential, etsy_credential = _build_staging_credentials()

    products = create_sku(images[:1], credential=printify_credential, require_live=True)
    assert products and products[0].get("sku"), "No SKU returned from Printify stage"
    assert all(
        not str(item.get("sku", "")).startswith("stub-sku-") for item in products
    ), "Printify stage returned stub SKUs"

    listing = publish_listing(products[0], credential=etsy_credential, require_live=True)
    listing_id = str(listing.get("listing_id", "")).strip()
    listing_url = str(listing.get("etsy_url") or listing.get("listing_url") or "").strip()
    assert listing_id, "No listing ID returned from Etsy stage"
    assert not listing_id.startswith("stub"), "Etsy stage returned a stub listing ID"
    assert listing_url, "No Etsy listing URL returned from Etsy stage"
    assert not listing_url.startswith("https://etsy.example/"), "Etsy stage returned a stub listing URL"
