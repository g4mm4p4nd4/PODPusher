import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from services.analytics.api import app as analytics_app
from services.analytics.service import list_events, log_event
from services.common.database import init_db


@pytest.mark.asyncio
async def test_mock_keywords_endpoint_returns_sorted_top_10():
    await init_db()
    transport = ASGITransport(app=analytics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/analytics")
    assert resp.status_code == 200
    payload = resp.json()
    assert 1 <= len(payload) <= 10
    clicks = [item["clicks"] for item in payload]
    assert clicks == sorted(clicks, reverse=True)
    assert all("term" in item and "clicks" in item for item in payload)


@pytest.mark.asyncio
async def test_event_logging_and_summary():
    await init_db()
    transport = ASGITransport(app=analytics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/analytics/events",
            json={"event_type": "click", "path": "/home"},
        )
        assert resp.status_code == 201
        created = resp.json()
        assert created["event_type"] == "click"

        resp = await client.get("/api/analytics/summary")
        assert resp.status_code == 200
        summary = resp.json()
        assert summary[0]["path"] == "/home"
        assert summary[0]["clicks"] == 1


@pytest.mark.asyncio
async def test_middleware_logs_page_view():
    await init_db()
    transport = ASGITransport(app=analytics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/notfound")
    events = await list_events("page_view")
    assert any(e.path == "/notfound" for e in events)


@pytest.mark.asyncio
async def test_conversion_triggers_stripe(monkeypatch):
    await init_db()
    called = False

    async def fake_report(quantity: int = 1) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(
        "services.analytics.service._report_conversion_to_stripe", fake_report
    )

    await log_event("conversion", "/checkout")
    await asyncio.sleep(0)
    assert called
