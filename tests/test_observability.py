import pytest
from httpx import AsyncClient, ASGITransport

from services.gateway.api import app as gateway_app
from services.auth.api import app as auth_app


@pytest.mark.asyncio
async def test_gateway_health_and_metrics():
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        metrics = await client.get("/metrics")
        assert metrics.status_code == 200
        body = metrics.text
        assert "pod_request_total" in body


@pytest.mark.asyncio
async def test_auth_health_and_metrics():
    transport = ASGITransport(app=auth_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        metrics = await client.get("/metrics")
        assert metrics.status_code == 200
        assert "pod_request_total" in metrics.text
