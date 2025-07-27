import pytest
from httpx import AsyncClient, ASGITransport
from services.gateway.api import app as gateway_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_product_not_found_spanish_message():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/images/review/999",
            json={},
            headers={"Accept-Language": "es"},
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Producto no encontrado"
