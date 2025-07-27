import pytest
from services.search.service import search_products
from services.common.database import init_db, get_session
from services.models import Trend, Idea, Product


@pytest.mark.asyncio
async def test_search_products():
    await init_db()
    async with get_session() as session:
        trend = Trend(term="cat mug", category="animals")
        session.add(trend)
        await session.commit()
        await session.refresh(trend)
        idea = Idea(trend_id=trend.id, description="Cute cat mug")
        session.add(idea)
        await session.commit()
        await session.refresh(idea)
        prod = Product(idea_id=idea.id, image_url="url", rating=5, tags=["cute"])
        session.add(prod)
        await session.commit()
        await session.refresh(prod)
        prod_id = prod.id
    res = await search_products(q="cat", category="animals", rating_min=4)
    assert res["total"] == 1
    assert res["items"][0]["id"] == prod_id
