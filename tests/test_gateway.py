import pytest
from httpx import AsyncClient, ASGITransport
from services.gateway.api import app as gateway_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_generate_response():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/generate", headers={"X-User-Id": "1"})
        assert resp.status_code == 200
        data = resp.json()
        assert "listing_url" in data
        assert "events" in data
        assert data.get("trends")
        assert data.get("ideas")
        assert data.get("products")
        assert "auth" in data
        assert "missing" in data["auth"]
        assert data["auth"]["user_id"] == 1
