import pytest
from httpx import AsyncClient, ASGITransport
from services.analytics.api import app as analytics_app


@pytest.mark.asyncio
async def test_analytics_endpoint():
    transport = ASGITransport(app=analytics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 10
        first = data[0]
        assert "keyword" in first and "clicks" in first
