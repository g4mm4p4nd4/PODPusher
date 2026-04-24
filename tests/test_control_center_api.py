from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import select

from services.common.database import get_session, init_db
from services.gateway.api import app as gateway_app
from services.models import BrandProfile, TrendSignal


@pytest.mark.asyncio
async def test_overview_and_trend_insights_include_provenance():
    await init_db()
    async with get_session() as session:
        session.add(
            TrendSignal(
                source="unit",
                keyword="dog mom",
                category="Apparel",
                engagement_score=1000,
                timestamp=datetime.utcnow(),
            )
        )
        await session.commit()

    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        overview = await client.get(
            "/api/dashboard/overview", headers={"X-User-Id": "1"}
        )
        assert overview.status_code == 200
        body = overview.json()
        assert body["metrics"]
        assert body["metrics"][0]["provenance"]["source"] == "trend_signals"

        trends = await client.get("/api/trends/insights")
        assert trends.status_code == 200
        trend_body = trends.json()
        assert trend_body["keywords"]
        assert "provenance" in trend_body["keywords"][0]


@pytest.mark.asyncio
async def test_niche_profile_persistence_and_suggestions():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        profile = await client.post(
            "/api/niches/profile",
            json={
                "tone": "Minimal, Calm",
                "audience": "Outdoor Buyers",
                "interests": ["Outdoors"],
            },
            headers={"X-User-Id": "7"},
        )
        assert profile.status_code == 200
        assert profile.json()["tone"] == "Minimal, Calm"

        suggestions = await client.get(
            "/api/niches/suggestions", headers={"X-User-Id": "7"}
        )
        assert suggestions.status_code == 200
        assert suggestions.json()["niches"]

    async with get_session() as session:
        saved = (
            await session.exec(select(BrandProfile).where(BrandProfile.user_id == 7))
        ).all()
        assert saved


@pytest.mark.asyncio
async def test_listing_composer_generate_score_and_compliance():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        generated = await client.post(
            "/api/listing-composer/generate",
            json={"niche": "Dog Mom Gifts", "primary_keyword": "dog mom"},
        )
        assert generated.status_code == 200
        payload = generated.json()
        assert "dog mom" in payload["title"].lower()
        assert payload["score"]["optimization_score"] > 0

        compliance = await client.post(
            "/api/listing-composer/compliance",
            json={
                "title": payload["title"],
                "description": payload["description"],
                "tags": payload["tags"],
            },
        )
        assert compliance.status_code == 200
        assert compliance.json()["status"] == "compliant"


@pytest.mark.asyncio
async def test_seasonal_search_ab_notifications_and_settings_dashboards():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        seasonal = await client.get("/api/seasonal/events", headers={"X-User-Id": "1"})
        assert seasonal.status_code == 200
        assert seasonal.json()["events"]

        search = await client.get("/api/search/insights", params={"q": "dog"})
        assert search.status_code == 200
        assert search.json()["results"]

        ab = await client.get("/api/ab-tests/dashboard")
        assert ab.status_code == 200
        assert ab.json()["experiments"]

        notifications = await client.get(
            "/api/notifications/dashboard", headers={"X-User-Id": "1"}
        )
        assert notifications.status_code == 200
        assert notifications.json()["scheduled_jobs"]

        settings = await client.get(
            "/api/settings/dashboard", headers={"X-User-Id": "1"}
        )
        assert settings.status_code == 200
        assert settings.json()["localization"]["default_language"]
