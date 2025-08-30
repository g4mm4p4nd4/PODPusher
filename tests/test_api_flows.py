import pytest
from httpx import AsyncClient, ASGITransport
from services.common import database
from services.user.api import app as user_app
from services.gateway.api import app as gateway_app
from services.image_gen.api import app as image_app
from services.image_review.api import app as review_app
from services.search.api import app as search_app
from services.ab_tests.api import app as ab_app
from services.analytics.api import app as analytics_app
from services.notifications.api import app as notif_app
from services.notifications.service import weekly_trending_summary


@pytest.fixture(autouse=True)
async def _setup_db(monkeypatch):
    monkeypatch.setattr(database, "DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    await database.init_db()
    yield


@pytest.mark.asyncio
async def test_user_registration_and_listing():
    transport_user = ASGITransport(app=user_app)
    async with AsyncClient(transport=transport_user, base_url="http://test") as client:
        resp = await client.get("/api/user/plan", headers={"X-User-Id": "1"})
        assert resp.status_code == 200
    transport_gateway = ASGITransport(app=gateway_app)
    async with AsyncClient(
        transport=transport_gateway, base_url="http://test"
    ) as client:
        resp = await client.post("/generate")
        assert resp.status_code == 200
        assert "listing_url" in resp.json()


@pytest.mark.asyncio
async def test_image_review_and_tagging():
    transport_image = ASGITransport(app=image_app)
    async with AsyncClient(transport=transport_image, base_url="http://test") as client:
        resp = await client.post(
            "/images", json={"ideas": ["idea"]}, headers={"X-User-Id": "2"}
        )
        assert resp.status_code == 200
    transport_review = ASGITransport(app=review_app)
    async with AsyncClient(
        transport=transport_review, base_url="http://test"
    ) as client:
        resp = await client.get("/")
        products = resp.json()
        assert products
        prod_id = products[0]["id"]
        resp = await client.post(f"/{prod_id}", json={"rating": 5, "tags": ["x"]})
        assert resp.status_code == 200
        resp = await client.post("/999", json={"rating": 1})
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_search_with_i18n():
    transport_image = ASGITransport(app=image_app)
    async with AsyncClient(transport=transport_image, base_url="http://test") as client:
        await client.post(
            "/images", json={"ideas": ["cat"]}, headers={"X-User-Id": "3"}
        )
    transport_search = ASGITransport(app=search_app)
    async with AsyncClient(
        transport=transport_search, base_url="http://test"
    ) as client:
        resp = await client.get(
            "/", params={"q": "cat"}, headers={"Accept-Language": "es"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_ab_testing_flow():
    transport = ASGITransport(app=ab_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/",
            json={
                "name": "t",
                "experiment_type": "image",
                "variants": [
                    {"name": "a", "weight": 0.5},
                    {"name": "b", "weight": 0.5},
                ],
            },
        )
        assert resp.status_code == 200
        test_id = resp.json()["id"]
        variant_id = resp.json()["variants"][0]["id"]
        await client.post(f"/{variant_id}/impression")
        resp = await client.get(f"/{test_id}/metrics")
        assert resp.status_code == 200
        assert resp.json()[0]["impressions"] == 1


@pytest.mark.asyncio
async def test_analytics_event_flow():
    transport = ASGITransport(app=analytics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/analytics/events", json={"event_type": "click", "path": "/"}
        )
        assert resp.status_code == 201
        resp = await client.get("/analytics/events")
        assert any(e["path"] == "/" for e in resp.json())


@pytest.mark.asyncio
async def test_notifications_scheduling(monkeypatch):
    transport = ASGITransport(app=notif_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/", json={"message": "hi"}, headers={"X-User-Id": "5"}
        )
        assert resp.status_code == 200
    from services.common.database import get_session
    from services.models import User

    async with get_session() as session:
        session.add(User(id=5))
        await session.commit()

    async def fake_fetch_trends(category=None):
        return [{"term": "foo", "category": "general"}]

    monkeypatch.setattr(
        "services.notifications.service.fetch_trends", fake_fetch_trends
    )
    await weekly_trending_summary()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/", headers={"X-User-Id": "5"})
        assert any("Weekly trending" in n["message"] for n in resp.json())
