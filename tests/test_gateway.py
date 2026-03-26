import pytest
import sys
import types
from httpx import ASGITransport, AsyncClient

from services.common.database import get_session, init_db
from services.models import Idea, Trend, User

if "stripe" not in sys.modules:
    sys.modules["stripe"] = types.SimpleNamespace(
        api_key=None,
        Customer=types.SimpleNamespace(search=lambda **_: types.SimpleNamespace(data=[])),
        Subscription=types.SimpleNamespace(list=lambda **_: types.SimpleNamespace(data=[])),
        billing_portal=types.SimpleNamespace(
            Session=types.SimpleNamespace(create=lambda **_: types.SimpleNamespace(url="https://stub"))
        ),
        error=types.SimpleNamespace(
            StripeError=Exception,
            InvalidRequestError=Exception,
        ),
    )

from services.gateway.api import app as gateway_app


@pytest.mark.asyncio
async def test_generate_response_without_oauth():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/generate", headers={"X-User-Id": "1"})
    assert resp.status_code == 200
    data = resp.json()
    assert "listing_url" in data
    assert data["listing"] is None
    assert data["listing_url"] is None
    assert data.get("trends")
    assert data.get("ideas")
    assert data.get("products")
    assert set(data["auth"]["missing"]) == {"printify", "etsy"}
    assert data["auth"]["user_id"] == 1
    assert data["auth"]["printify_linked"] is False
    assert data["auth"]["etsy_linked"] is False


@pytest.mark.asyncio
async def test_generate_with_linked_oauth(monkeypatch):
    await init_db()

    async def fake_load(user_id, provider):
        return {"access_token": f"{provider.value}-token"}

    def fake_create_sku(products, credential=None):
        assert credential is not None
        return [{**products[0], "id": "prod-1"}]

    def fake_publish_listing(product, credential=None):
        assert credential is not None
        return {
            "id": "listing-1",
            "etsy_url": "https://etsy.test/listing-1",
            "title": product.get("title", "Generated Listing"),
        }

    monkeypatch.setattr("services.gateway.api.load_oauth_credentials", fake_load)
    monkeypatch.setattr("services.gateway.api.create_sku", fake_create_sku)
    monkeypatch.setattr("services.gateway.api.publish_listing", fake_publish_listing)

    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/generate", headers={"X-User-Id": "42"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["auth"]["missing"] == []
    assert data["auth"]["printify_linked"] is True
    assert data["auth"]["etsy_linked"] is True
    assert data["listing_url"] == "https://etsy.test/listing-1"
    assert data["listing"]["listing_url"] == "https://etsy.test/listing-1"
    assert data["products"] and data["products"][0]["id"] == "prod-1"


@pytest.mark.asyncio
async def test_gateway_exposes_user_and_analytics_routes():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        user_resp = await client.get("/api/user/me", headers={"X-User-Id": "9"})
        analytics_resp = await client.get("/api/analytics")

    assert user_resp.status_code == 200
    assert user_resp.json()["plan"] == "free"
    assert analytics_resp.status_code == 200
    assert isinstance(analytics_resp.json(), list)


@pytest.mark.asyncio
async def test_generate_rejects_invalid_bearer_even_with_user_header():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/generate",
            headers={
                "Authorization": "Bearer invalid-token",
                "X-User-Id": "9",
            },
        )
    assert resp.status_code == 401
    body = resp.json()
    assert body["code"] == "UNAUTHORIZED"
    assert body["message"] == "Authentication required"


async def _seed_image_idea(description: str = "cat shirt", category: str = "animals") -> int:
    async with get_session() as session:
        trend = Trend(term="cat", category=category)
        session.add(trend)
        await session.commit()
        await session.refresh(trend)

        idea = Idea(trend_id=trend.id, description=description)
        session.add(idea)
        await session.commit()
        await session.refresh(idea)
        return int(idea.id)


@pytest.mark.asyncio
async def test_gateway_image_generation_endpoints(monkeypatch):
    await init_db()
    idea_id = await _seed_image_idea()

    async def fake_generate_image(_prompt: str) -> str:
        return "https://example.com/generated.png"

    monkeypatch.setattr("services.image_gen.service.openai.generate_image", fake_generate_image)

    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        generate_resp = await client.post(
            "/api/images/generate",
            json={"idea_id": idea_id, "style": "editorial"},
            headers={"X-User-Id": "55"},
        )
        assert generate_resp.status_code == 200
        generated = generate_resp.json()
        assert generated[0]["provider"] == "openai"
        image_id = generated[0]["id"]

        list_resp = await client.get(
            "/api/images",
            params={"idea_id": idea_id},
            headers={"X-User-Id": "55"},
        )
        assert list_resp.status_code == 200
        listed = list_resp.json()
        assert listed[0]["id"] == image_id

        delete_resp = await client.delete(
            f"/api/images/{image_id}",
            headers={"X-User-Id": "55"},
        )
        assert delete_resp.status_code == 200
        assert delete_resp.json() == {"status": "deleted"}


@pytest.mark.asyncio
async def test_gateway_image_generation_respects_quota():
    await init_db()
    idea_id = await _seed_image_idea()

    async with get_session() as session:
        user = User(id=91, plan="free", quota_used=20, quota_limit=20)
        session.add(user)
        await session.commit()

    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/images/generate",
            json={"idea_id": idea_id, "style": "default"},
            headers={"X-User-Id": "91"},
        )

    assert resp.status_code == 403
    assert resp.json()["code"] == "QUOTA_EXCEEDED"
