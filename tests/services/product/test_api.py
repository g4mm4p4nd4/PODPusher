import pytest
from httpx import ASGITransport, AsyncClient

from services.common.database import get_session, init_db
from services.gateway.api import app as gateway_app
from services.models import Product


@pytest.mark.asyncio
async def test_product_review_get_and_update():
    await init_db()

    async with get_session() as session:
        product = Product(idea_id=1, image_url="https://example.com/a.png")
        session.add(product)
        await session.commit()
        await session.refresh(product)
        product_id = product.id

    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/products/review")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data
        assert data[0]["id"] == product_id

        update_response = await client.put(
            f"/api/products/{product_id}",
            json={"rating": 5, "tags": ["tag1"], "flagged": False},
        )
        assert update_response.status_code == 200
        payload = update_response.json()
        assert payload["rating"] == 5
        assert payload["tags"] == ["tag1"]
        assert payload["flagged"] is False

        invalid_response = await client.put(
            f"/api/products/{product_id}",
            json={"rating": 6},
        )
        assert invalid_response.status_code == 422
