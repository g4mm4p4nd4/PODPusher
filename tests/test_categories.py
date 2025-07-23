import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # noqa: E402

import pytest  # noqa: E402
from httpx import AsyncClient, ASGITransport  # noqa: E402
from services.gateway.api import app as gateway_app  # noqa: E402


@pytest.mark.asyncio
async def test_product_categories_endpoint():
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/product-categories")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 5
        apparel = next((c for c in data if c["name"] == "apparel"), None)
        assert apparel is not None
        assert any("unisex t-shirts" in item for item in apparel["items"])
