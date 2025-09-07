import io
import json
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from services.common.monitoring import setup_observability
from services.common.logging import logger


@pytest.mark.asyncio
async def test_correlation_id_logged():
    app = FastAPI()
    setup_observability(app)

    @app.get("/ping")
    async def ping():
        return {"pong": True}

    stream = io.StringIO()
    handler_id = logger.add(stream, serialize=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cid = "test-id"
        await client.get("/ping", headers={"X-Correlation-ID": cid})

    logger.remove(handler_id)
    log_line = stream.getvalue().strip().split("\n")[-1]
    data = json.loads(log_line)
    extra = data["record"]["extra"]
    assert extra["correlation_id"] == "test-id"
    assert extra["method"] == "GET"
    assert extra["path"] == "/ping"
    assert extra["status"] == 200


@pytest.mark.asyncio
async def test_health_ready_and_metrics():
    app = FastAPI()
    setup_observability(app)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200

        async def fail():
            return False

        with patch("services.common.monitoring.check_db_connection", fail):
            resp = await client.get("/ready")
            assert resp.status_code == 503

        await client.get("/health")
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        assert "http_requests_total" in resp.text
