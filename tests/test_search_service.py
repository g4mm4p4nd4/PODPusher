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

    results = await search_products(
        q="dog", category="apparel", tag="funny", rating_min=3
    )
    assert results["total"] == 1
    assert results["items"][0]["id"] == product.id


@pytest.mark.asyncio
async def test_search_pagination():
    await init_db()
    async with get_session() as session:
        trend = Trend(term="cat", category="apparel")
        session.add(trend)
        await session.commit()
        await session.refresh(trend)
        idea = Idea(trend_id=trend.id, description="funny cat shirt")
        session.add(idea)
        await session.commit()
        await session.refresh(idea)
        p1 = Product(idea_id=idea.id, image_url="1.png", rating=5, tags=["cat"])
        p2 = Product(idea_id=idea.id, image_url="2.png", rating=5, tags=["cat"])
        session.add(p1)
        session.add(p2)
        await session.commit()
        await session.refresh(p2)
        second_id = p2.id

    results = await search_products(q="cat", page=2, page_size=1)
    assert results["page"] == 2
    assert len(results["items"]) == 1
    assert results["items"][0]["id"] == second_id
