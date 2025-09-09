import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # noqa: E402,E501

import pytest  # noqa: E402

from services.trend_scraper.service import fetch_trends  # noqa: E402
from services.ideation.service import generate_ideas  # noqa: E402
from services.image_gen.service import generate_images  # noqa: E402
from services.models import Idea  # noqa: E402
from services.common.database import get_session  # noqa: E402
from services.integration.service import create_sku, publish_listing  # noqa: E402
from services.common.database import init_db  # noqa: E402


@pytest.mark.asyncio
async def test_full_pipeline(monkeypatch):
    await init_db()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    trends = await fetch_trends()
    assert trends
    ideas = await generate_ideas([t["term"] for t in trends])
    assert ideas
    image_dicts = []
    async with get_session() as session:
        for i in ideas:
            idea = Idea(trend_id=0, description=i["description"])
            session.add(idea)
            await session.commit()
            await session.refresh(idea)
            urls = await generate_images(idea.id, "default")
            image_dicts.extend([{"image_url": u} for u in urls])
    assert image_dicts
    products = create_sku(image_dicts)
    assert all("sku" in p for p in products)
    listing = publish_listing(products[0])
    assert "etsy_url" in listing
