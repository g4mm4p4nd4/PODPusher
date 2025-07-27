import pytest
from httpx import AsyncClient, ASGITransport

from services.gateway.api import app as gateway_app
from services.image_gen.service import generate_images
from services.common.database import init_db


@pytest.mark.asyncio
async def test_image_review_endpoints():
    await init_db()
    # seed one product
    await generate_images(["test idea"])

    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/images/review/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data
        prod_id = data[0]["id"]

        resp2 = await client.post(
            f"/api/images/review/{prod_id}",
            json={"rating": 5, "tags": ["tag1"], "flagged": False},
        )
        assert resp2.status_code == 200
        updated = resp2.json()
        assert updated["rating"] == 5
        assert updated["tags"] == ["tag1"]
        assert updated["flagged"] is False
