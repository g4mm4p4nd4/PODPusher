from datetime import timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from services.common.database import get_session, init_db
from services.common.time import utcnow
from services.gateway.api import app as gateway_app
from services.models import TrendSignal


@pytest.mark.asyncio
async def test_live_trends_endpoint():
    await init_db()
    now = utcnow()
    async with get_session() as session:
        session.add(
            TrendSignal(
                source="tiktok",
                keyword="funny cat",
                engagement_score=5,
                category="animals",
                timestamp=now,
                metadata_json={
                    "method": "selector_fallback",
                    "market_examples": [
                        {
                            "title": "Funny Cat Shirt Example",
                            "keyword": "funny cat",
                            "source": "tiktok",
                            "source_url": "https://example.com/funny-cat",
                            "image_url": "https://example.com/funny-cat.jpg",
                            "engagement_score": 5,
                            "example_type": "source_trend",
                            "provenance": {
                                "source": "tiktok",
                                "is_estimated": False,
                                "updated_at": now.isoformat(),
                                "confidence": 0.82,
                            },
                        }
                    ],
                },
            )
        )
        session.add(
            TrendSignal(
                source="twitter",
                keyword="climate",
                engagement_score=3,
                category="activism",
                timestamp=now,
            )
        )
        session.add(
            TrendSignal(
                source="tiktok",
                keyword="ancient",
                engagement_score=500,
                category="animals",
                timestamp=now - timedelta(hours=90),
            )
        )
        await session.commit()

    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/trends/live")
        assert resp.status_code == 200
        data = resp.json()
        assert "animals" in data
        assert data["animals"][0]["keyword"] == "funny cat"

        resp = await client.get("/api/trends/live", params={"category": "activism"})
        assert resp.status_code == 200
        filtered = resp.json()
        assert list(filtered.keys()) == ["activism"]

        resp = await client.get(
            "/api/trends/live",
            params={
                "source": "tiktok",
                "lookback_hours": 48,
                "limit": 1,
                "include_meta": True,
                "sort_by": "timestamp",
            },
        )
        assert resp.status_code == 200
        filtered = resp.json()
        assert list(filtered["items_by_category"].keys()) == ["animals"]
        assert filtered["items_by_category"]["animals"][0]["source"] == "tiktok"
        assert filtered["items_by_category"]["animals"][0]["provenance"]["source"] == "tiktok"
        assert (
            filtered["items_by_category"]["animals"][0]["market_examples"][0]["title"]
            == "Funny Cat Shirt Example"
        )
        assert filtered["items_by_category"]["animals"][0]["method"] == "selector_fallback"
        assert filtered["pagination"]["sort_by"] == "timestamp"


@pytest.mark.asyncio
async def test_live_trends_endpoint_rejects_invalid_limits():
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/trends/live", params={"lookback_hours": 0})
        assert resp.status_code == 422

        resp = await client.get("/api/trends/live", params={"limit": 51})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_refresh_and_status_endpoint(monkeypatch):
    await init_db()

    async def fake_refresh():
        async with get_session() as session:
            session.add(
                TrendSignal(
                    source="etsy",
                    keyword="handmade",
                    engagement_score=1,
                    category="other",
                )
            )
            await session.commit()
        return {
            "last_started_at": "2026-03-06T10:00:00",
            "last_finished_at": "2026-03-06T10:00:02",
            "last_mode": "live",
            "sources_succeeded": ["etsy"],
            "sources_failed": {},
            "source_methods": {"etsy": "selector_fallback"},
            "source_diagnostics": {
                "etsy": {
                    "status": "success",
                    "method": "selector_fallback",
                    "collected": 1,
                    "persisted": 1,
                }
            },
            "signals_collected": 1,
            "signals_persisted": 1,
        }

    monkeypatch.setattr("services.gateway.api.refresh_trends", fake_refresh)
    monkeypatch.setattr(
        "services.gateway.api.get_refresh_status",
        lambda: {
            "last_started_at": "2026-03-06T10:00:00",
            "last_finished_at": "2026-03-06T10:00:02",
            "last_mode": "live",
            "sources_succeeded": ["etsy"],
            "sources_failed": {},
            "source_methods": {"etsy": "selector_fallback"},
            "source_diagnostics": {
                "etsy": {
                    "status": "success",
                    "method": "selector_fallback",
                    "collected": 1,
                    "persisted": 1,
                }
            },
            "signals_collected": 1,
            "signals_persisted": 1,
        },
    )

    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/trends/refresh")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["last_mode"] == "live"
        assert payload["signals_persisted"] == 1

        status = await client.get("/api/trends/live/status")
        assert status.status_code == 200
        status_data = status.json()
        assert status_data["last_mode"] == "live"
        assert status_data["source_diagnostics"]["etsy"]["persisted"] == 1

        live = await client.get("/api/trends/live", params={"lookback_hours": 240})
        data = live.json()
        assert "other" in data
