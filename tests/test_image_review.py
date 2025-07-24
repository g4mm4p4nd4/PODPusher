import pytest
from httpx import AsyncClient, ASGITransport
from services.image_review.api import app as review_app
from services.gateway.api import app as gateway_app
from services.common.database import init_db
from services.models import Product
from services.common.database import get_session


@pytest.mark.asyncio
async def test_review_crud():
    await init_db()
    async with get_session() as session:
        p = Product(idea_id=1, image_url="http://example.com/img.png")
        session.add(p)
        await session.commit()
        await session.refresh(p)

    transport = ASGITransport(app=review_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/images/review")
        assert resp.status_code == 200
        data = resp.json()
        assert any(item["id"] == p.id for item in data)

        resp = await client.post(
            f"/images/review/{p.id}",
            json={"rating": 5, "tags": ["fun"], "flagged": False},
        )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["rating"] == 5
        assert updated["tags"] == "fun"

    g_transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=g_transport, base_url="http://test") as client:
        resp = await client.get("/api/images/review")
        assert resp.status_code == 200
        data = resp.json()
        assert any(item["id"] == p.id and item["rating"] == 5 for item in data)
