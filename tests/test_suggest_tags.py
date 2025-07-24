import pytest
from httpx import AsyncClient, ASGITransport
from services.gateway.api import app as gateway_app


@pytest.mark.asyncio
async def test_suggest_tags_endpoint():
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/suggest-tags", json={"description": "cute cat mug"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data
