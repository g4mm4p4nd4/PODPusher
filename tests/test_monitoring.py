import json
import logging
import pytest
from httpx import AsyncClient, ASGITransport
from services.gateway.api import app as gateway_app
from services.common.database import init_db
from services.logging import JsonFormatter


@pytest.mark.asyncio
async def test_health_ready_metrics_and_logging(caplog):
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        resp = await client.get("/ready")
        assert resp.status_code == 200
        # trigger metrics
        await client.get("/health")
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        assert "request_count" in resp.text

    with caplog.at_level(logging.INFO, logger="services.logging"):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.get(
                "/health",
                headers={"X-Request-ID": "req-1", "X-User-Id": "42"},
            )
    record = next(r for r in reversed(caplog.records) if r.name == "services.logging")
    data = json.loads(JsonFormatter().format(record))
    for field in ["timestamp", "level", "module", "message"]:
        assert field in data
    assert data["request_id"] == "req-1"
    assert data["user_id"] == "42"
