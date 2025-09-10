import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # noqa: E402,E501

import pytest  # noqa: E402

from services.trend_scraper.service import fetch_trends  # noqa: E402
from services.ideation.service import generate_ideas  # noqa: E402
from services.image_gen.service import generate_images  # noqa: E402
from services.common.database import get_session
from services.models import Idea
from sqlmodel import select
from services.integration.service import create_sku, publish_listing  # noqa: E402
from services.common.database import init_db  # noqa: E402


@pytest.mark.asyncio
async def test_full_pipeline(monkeypatch):
    await init_db()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    trends = await fetch_trends()
    assert trends
    await generate_ideas([t["term"] for t in trends])
    async with get_session() as session:
        result = await session.exec(select(Idea))
        idea_ids = [i.id for i in result.all()]
    images = []
    for iid in idea_ids:
        images.extend([{ "image_url": url } for url in await generate_images(iid, "default")])
    assert images
    products = create_sku(images)
    assert all("sku" in p for p in products)
    listing = publish_listing(products[0])
    assert "etsy_url" in listing
