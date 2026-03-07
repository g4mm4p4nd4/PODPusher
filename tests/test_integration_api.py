import pytest
from httpx import ASGITransport, AsyncClient

from services.integration.api import app as integration_app


@pytest.mark.asyncio
async def test_sku_endpoint_loads_printify_credential(monkeypatch):
    async def fake_load_oauth_credentials(user_id, provider):
        assert user_id == 42
        assert provider.value == "printify"
        return {"access_token": "printify-token", "account_id": "shop-1"}

    def fake_create_sku(products, credential=None):
        assert credential is not None
        assert credential["access_token"] == "printify-token"
        return [{**products[0], "sku": "sku-123"}]

    monkeypatch.setattr("services.integration.api.load_oauth_credentials", fake_load_oauth_credentials)
    monkeypatch.setattr("services.integration.api.create_sku", fake_create_sku)

    transport = ASGITransport(app=integration_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/sku",
            headers={"X-User-Id": "42"},
            json={"products": [{"title": "Test", "image_url": "https://example.com/image.png"}]},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["sku"] == "sku-123"


@pytest.mark.asyncio
async def test_listing_endpoint_loads_etsy_credential(monkeypatch):
    async def fake_load_oauth_credentials(user_id, provider):
        assert user_id == 7
        assert provider.value == "etsy"
        return {"access_token": "etsy-token", "account_id": "shop-7"}

    def fake_publish_listing(product, credential=None):
        assert credential is not None
        assert credential["access_token"] == "etsy-token"
        return {
            **product,
            "listing_id": "listing-1",
            "etsy_url": "https://etsy.test/listing-1",
            "listing_url": "https://etsy.test/listing-1",
        }

    monkeypatch.setattr("services.integration.api.load_oauth_credentials", fake_load_oauth_credentials)
    monkeypatch.setattr("services.integration.api.publish_listing", fake_publish_listing)

    transport = ASGITransport(app=integration_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/listing",
            headers={"X-User-Id": "7"},
            json={"title": "Launch"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["listing_id"] == "listing-1"
    assert payload["listing_url"] == "https://etsy.test/listing-1"


@pytest.mark.asyncio
async def test_legacy_endpoints_require_authentication():
    transport = ASGITransport(app=integration_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sku_response = await client.post(
            "/create-sku",
            json={"products": [{"title": "Test"}]},
        )
        listing_response = await client.post(
            "/publish-listing", json={"title": "Test"}
        )

    assert sku_response.status_code == 401
    assert listing_response.status_code == 401
