import pytest
from httpx import AsyncClient, ASGITransport
from services.gateway.api import app as gateway_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_bulk_create_endpoint():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"products": [{"name": "a"}, {"name": "b"}]}
        resp = await client.post("/api/bulk_create", json=payload)
        assert resp.status_code == 200
        assert resp.json()["created"] == 2
