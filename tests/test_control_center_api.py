import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import select

from services.common.database import get_session, init_db
from services.common.time import utcnow
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
                timestamp=utcnow(),
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


@pytest.mark.asyncio
async def test_page_filters_are_reflected_and_shape_backend_data():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        overview = await client.get(
            "/api/dashboard/overview",
            params={
                "date_from": "2026-04-01",
                "date_to": "2026-04-24",
                "store": "demo-store",
                "marketplace": "etsy",
                "country": "US",
                "language": "en",
                "category": "Apparel",
                "search": "dog",
            },
            headers={"X-User-Id": "22"},
        )
        assert overview.status_code == 200
        overview_body = overview.json()
        assert overview_body["filters"]["category"] == "Apparel"
        assert overview_body["filters"]["store"] == "demo-store"
        assert overview_body["integration_status"]["etsy"]["status"] in {
            "connected",
            "demo_fallback",
        }
        assert overview_body["actions_available"]
        assert overview_body["next_drilldowns"]
        assert all(
            "dog" in item["niche"].lower() or "dog" in item["provenance"]["source"]
            for item in overview_body["top_rising_niches"]
        )

        seasonal = await client.get(
            "/api/seasonal/events",
            params={
                "country": "US",
                "language": "en",
                "marketplace": "etsy",
                "category": "Mugs",
                "horizon_months": 12,
                "search": "mother",
            },
            headers={"X-User-Id": "22"},
        )
        assert seasonal.status_code == 200
        seasonal_body = seasonal.json()
        assert seasonal_body["filters"]["country"] == "US"
        assert seasonal_body["filters"]["category"] == "Mugs"
        assert seasonal_body["actions_available"]
        assert all(
            "mother" in event["name"].lower() for event in seasonal_body["events"]
        )

        niches = await client.get(
            "/api/niches/suggestions",
            params={"category": "Apparel", "search": "dog", "country": "US"},
            headers={"X-User-Id": "22"},
        )
        assert niches.status_code == 200
        niche_body = niches.json()
        assert niche_body["filters"]["search"] == "dog"
        assert niche_body["actions_available"]
        assert all(item["category"] == "Apparel" for item in niche_body["niches"])

        search = await client.get(
            "/api/search/insights",
            params={
                "q": "dog",
                "category": "Apparel",
                "rating_min": 4.7,
                "price_max": 20,
                "marketplace": "etsy",
                "country": "US",
                "language": "en",
            },
            headers={"X-User-Id": "22"},
        )
        assert search.status_code == 200
        search_body = search.json()
        assert search_body["filters"]["rating_min"] == 4.7
        assert search_body["filters"]["price_max"] == 20
        assert search_body["actions_available"]
        assert all(result["rating"] >= 4.7 for result in search_body["results"])
        assert all(result["price"] <= 20 for result in search_body["results"])


@pytest.mark.asyncio
async def test_search_and_saved_state_mutations_persist_demo_state():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        saved = await client.post(
            "/api/search/saved",
            json={
                "name": "Dog Mom Apparel",
                "query": "dog mom",
                "filters": {"category": "Apparel", "price_max": 25},
                "result_count": 3,
            },
            headers={"X-User-Id": "44"},
        )
        assert saved.status_code == 200
        assert saved.json()["state"] == "persisted"
        assert saved.json()["filters"]["price_max"] == 25

        watchlist = await client.post(
            "/api/search/watchlist",
            json={
                "item_type": "keyword",
                "name": "dog mom",
                "context": {"trend_score": 92},
            },
            headers={"X-User-Id": "44"},
        )
        assert watchlist.status_code == 200
        assert watchlist.json()["state"] == "persisted"
        assert watchlist.json()["context"]["trend_score"] == 92

        state = await client.post(
            "/api/search/state",
            json={
                "name": "Comparison",
                "query": "dog mom",
                "selected_ids": [1, 2],
                "view": "compare",
                "result_count": 2,
            },
            headers={"X-User-Id": "44"},
        )
        assert state.status_code == 200
        assert state.json()["kind"] == "search_state"
        assert state.json()["filters"]["selected_ids"] == [1, 2]

        tags = await client.post(
            "/api/search/generate-tags",
            json={
                "keyword": "dog mom",
                "category": "Apparel",
                "seed_tags": ["fur mama"],
            },
            headers={"X-User-Id": "44"},
        )
        assert tags.status_code == 200
        tag_body = tags.json()
        assert tag_body["state"] == "persisted"
        assert "dog" in tag_body["tags"]
        assert tag_body["integration_status"]["openai"]["status"] in {
            "connected",
            "demo_fallback",
        }
