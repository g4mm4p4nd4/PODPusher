import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from services.analytics.api import app as analytics_app
from services.analytics.service import list_events, log_event
from services.common.database import get_session, init_db
from services.models import Trend, TrendSignal


@pytest.mark.asyncio
async def test_keywords_endpoint_aggregates_live_trend_signals():
    await init_db()
    async with get_session() as session:
        session.add(
            TrendSignal(source="tiktok", keyword="Funny Cat", engagement_score=5, category="animals")
        )
        session.add(
            TrendSignal(source="reddit", keyword="funny   cat", engagement_score=7, category="animals")
        )
        session.add(
            TrendSignal(source="etsy", keyword="dog mom", engagement_score=2, category="animals")
        )
        await session.commit()

    transport = ASGITransport(app=analytics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/analytics", params={"limit": 2})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload == [{"term": "funny cat", "clicks": 12}, {"term": "dog mom", "clicks": 2}]


@pytest.mark.asyncio
async def test_keywords_endpoint_falls_back_to_trend_terms_when_signals_missing():
    await init_db()
    async with get_session() as session:
        session.add(Trend(term="pet portrait", category="art"))
        session.add(Trend(term="pet portrait", category="art"))
        session.add(Trend(term="custom mug", category="home"))
        await session.commit()

    transport = ASGITransport(app=analytics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/analytics", params={"limit": 5})

    assert resp.status_code == 200
    payload = resp.json()
    assert payload[0] == {"term": "pet portrait", "clicks": 2}
    assert payload[1] == {"term": "custom mug", "clicks": 1}


@pytest.mark.asyncio
async def test_keywords_endpoint_rejects_invalid_query_values():
    await init_db()
    transport = ASGITransport(app=analytics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        bad_limit = await client.get("/api/analytics", params={"limit": 0})
        bad_window = await client.get("/api/analytics", params={"lookback_hours": 1000})

    assert bad_limit.status_code == 422
    assert bad_window.status_code == 422


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
