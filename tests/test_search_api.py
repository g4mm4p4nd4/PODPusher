import pytest
from httpx import AsyncClient, ASGITransport

from services.gateway.api import app as gateway_app
from services.common.database import init_db, get_session
from services.models import Trend, Idea, Product


@pytest.mark.asyncio
async def test_search_api_endpoint():
    await init_db()
    async with get_session() as session:
        t = Trend(term="cat mug", category="accessories")
        session.add(t)
        await session.commit()
        await session.refresh(t)
        idea = Idea(trend_id=t.id, description="cute cat mug")
        session.add(idea)
        await session.commit()
        await session.refresh(idea)
        prod = Product(
            idea_id=idea.id,
            image_url="img.png",
            rating=5,
            tags=["cute"],
        )
        session.add(prod)
        await session.commit()

    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/search/",
            params={
                "q": "cat",
                "category": "accessories",
                "tag": "cute",
                "rating_min": 4,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["image_url"] == "img.png"
