import pytest
from httpx import AsyncClient, ASGITransport
from services.analytics.api import app as analytics_app
from services.analytics.service import list_events
from services.common.database import init_db


@pytest.mark.asyncio
async def test_event_logging_and_summary():
    await init_db()
    transport = ASGITransport(app=analytics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/analytics/events",
            json={"event_type": "click", "path": "/home"},
        )
        assert resp.status_code == 201
        created = resp.json()
        assert created["event_type"] == "click"

        resp = await client.get("/analytics/summary", params={"event_type": "click"})
        assert resp.status_code == 200
        summary = resp.json()
        assert summary[0]["path"] == "/home"
        assert summary[0]["count"] == 1


@pytest.mark.asyncio
async def test_middleware_logs_page_view():
    await init_db()
    transport = ASGITransport(app=analytics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/analytics/summary")
    events = await list_events("page_view")
    assert any(e.path == "/analytics/summary" for e in events)


@pytest.mark.asyncio
async def test_metric_crud():
    await init_db()
    transport = ASGITransport(app=analytics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/analytics/metrics",
            json={"name": "visitors", "value": 10},
        )
        assert resp.status_code == 201
        created = resp.json()
        resp = await client.get("/analytics/metrics")
        assert resp.status_code == 200
        metrics = resp.json()
        assert any(m["id"] == created["id"] for m in metrics)
