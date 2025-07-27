import pytest
from httpx import AsyncClient, ASGITransport

from services.gateway.api import app as gateway_app
from services.common.database import init_db, get_session
from services.models import Trend, Idea, Product


@pytest.mark.asyncio
async def test_search_endpoint():
    await init_db()
    async with get_session() as session:
        trend = Trend(term="funny cat", category="animals")
        session.add(trend)
        await session.commit()
        await session.refresh(trend)
        idea = Idea(trend_id=trend.id, description="funny cat t-shirt")
        session.add(idea)
        await session.commit()
        await session.refresh(idea)
        product = Product(
            idea_id=idea.id, image_url="http://img", rating=4, tags=["cats", "funny"]
        )
        session.add(product)
        await session.commit()

    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/search", params={"q": "funny"})
        assert resp.status_code == 200
        data = resp.json()
        assert data
        assert data[0]["rating"] == 4
        resp = await client.get(
            "/api/search", params={"category": "animals", "rating_min": 5}
        )
        assert resp.status_code == 200
        assert resp.json() == []
