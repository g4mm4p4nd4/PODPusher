import pytest
from httpx import AsyncClient, ASGITransport
from services.gateway.api import app as gateway_app


@pytest.mark.asyncio
async def test_product_suggestions_endpoint():
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/product-suggestions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 5
        for item in data:
            assert "category" in item
            assert "design_theme" in item
            assert "suggestion" in item
