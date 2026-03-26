import json
import logging

import structlog
import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from services.common.database import init_db
from services.common.observability import register_observability
from services.ideation.api import app as ideation_app
from services.integration.api import app as integration_app
from services.listing_composer.api import app as listing_app
from services.product.api import app as product_app
from services.search.api import app as search_app
from services.social_generator.api import app as social_app
from services.user.api import app as user_app


def _build_logging_app() -> FastAPI:
    app = FastAPI()
    register_observability(app, service_name="logging-test")

    @app.get("/log")
    async def log_endpoint():
        structlog.get_logger("logging-test").info("inside-request")
        return {"ok": True}

    return app


@pytest.mark.asyncio
async def test_ready_endpoint_returns_service_status():
    await init_db()
    app = _build_logging_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ready = await client.get("/ready")
        assert ready.status_code == 200
        assert ready.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_ready_endpoint_returns_503_on_database_failure(monkeypatch):
    async def fake_database_ready() -> bool:
        return False

    monkeypatch.setattr("services.common.observability._database_ready", fake_database_ready)

    app = _build_logging_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ready = await client.get("/ready")
        assert ready.status_code == 503
        assert ready.json()["detail"] == "not ready"


@pytest.mark.asyncio
async def test_request_context_is_bound_and_cleared(caplog):
    app = _build_logging_app()
    transport = ASGITransport(app=app)

    with caplog.at_level(logging.INFO):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/log",
                headers={"X-Request-ID": "req-123", "X-User-Id": "42"},
            )
            assert response.status_code == 200
        structlog.get_logger("logging-test").info("outside-request")

    payloads = []
    for record in caplog.records:
        message = record.getMessage()
        if not message.startswith("{"):
            continue
        try:
            payloads.append(json.loads(message))
        except json.JSONDecodeError:
            continue

    inside = next(item for item in payloads if item.get("event") == "inside-request")
    assert inside["request_id"] == "req-123"
    assert inside["user_id"] == 42

    outside = next(item for item in payloads if item.get("event") == "outside-request")
    assert "request_id" not in outside
    assert "user_id" not in outside


@pytest.mark.asyncio
async def test_newly_instrumented_apps_expose_ready_and_metrics():
    await init_db()
    apps = [
        ideation_app,
        integration_app,
        listing_app,
        product_app,
        search_app,
        social_app,
        user_app,
    ]

    for app in apps:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            ready = await client.get("/ready")
            assert ready.status_code == 200
            assert ready.json() == {"status": "ready"}

            metrics = await client.get("/metrics")
            assert metrics.status_code == 200
            assert "pod_request_total" in metrics.text
