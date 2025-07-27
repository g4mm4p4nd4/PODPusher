import pytest

from services.search.service import search_products
from services.common.database import init_db, get_session
from services.models import Trend, Idea, Product


@pytest.mark.asyncio
async def test_search_service_filters():
    await init_db()
    async with get_session() as session:
        trend = Trend(term="dog", category="apparel")
        session.add(trend)
        await session.commit()
        await session.refresh(trend)
        idea = Idea(trend_id=trend.id, description="funny dog shirt")
        session.add(idea)
        await session.commit()
        await session.refresh(idea)
        product = Product(
            idea_id=idea.id,
            image_url="x.png",
            rating=4,
            tags=["funny", "dog"],
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)

    results = await search_products(q="dog", category="apparel", tag="funny", rating_min=3)
    assert len(results) == 1
    assert results[0]["id"] == product.id
