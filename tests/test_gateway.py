import pytest
from httpx import ASGITransport, AsyncClient

from services.common.database import init_db
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
