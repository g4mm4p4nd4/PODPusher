import pytest
from httpx import AsyncClient, ASGITransport

from services.gateway.api import app as gateway_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_bulk_upload_unsupported_file():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("products.txt", "bad", "text/plain")}
        resp = await client.post("/api/bulk_create", files=files)
        assert resp.status_code == 400
