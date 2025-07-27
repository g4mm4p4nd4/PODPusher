import pytest
from httpx import AsyncClient, ASGITransport
from services.gateway.api import app as gateway_app
from services.common.database import init_db, get_session
from services.models import Trend, Idea, Product


@pytest.mark.asyncio
async def test_search_endpoint():
    await init_db()
    async with get_session() as session:
        t = Trend(term="dog shirt", category="animals")
        session.add(t)
        await session.commit()
        await session.refresh(t)
        i = Idea(trend_id=t.id, description="Funny dog shirt")
        session.add(i)
        await session.commit()
        await session.refresh(i)
        p = Product(idea_id=i.id, image_url="url", rating=4, tags=["funny"])
        session.add(p)
        await session.commit()
        await session.refresh(p)
        p_id = p.id

    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/search/", params={"q": "dog", "rating_min": 4})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == p_id
