import pytest
from httpx import AsyncClient, ASGITransport
from services.gateway.api import app as gateway_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_monitoring_endpoints():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for path in ("/health", "/ready", "/metrics"):
            resp = await client.get(path)
            assert resp.status_code == 200
