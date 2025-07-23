import pytest
from httpx import AsyncClient, ASGITransport
from services.trend_scraper.api import app as trends_app


@pytest.mark.asyncio
async def test_trends_endpoint():
    transport = ASGITransport(app=trends_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/trends")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data

        resp = await client.get("/trends", params={"category": "animals"})
        assert resp.status_code == 200
        filtered = resp.json()
        assert all("animals" in t.get("category", "") for t in filtered)
