import pytest
from httpx import ASGITransport, AsyncClient

from services.integration.api import app as integration_app
from services.integration.service import (
    IntegrationCredentialError,
    IntegrationPayloadError,
    IntegrationUpstreamError,
)


@pytest.mark.asyncio
async def test_sku_endpoint_loads_printify_credential(monkeypatch):
    async def fake_load_oauth_credentials(user_id, provider):
        assert user_id == 42
        assert provider.value == "printify"
        return {"access_token": "printify-token", "account_id": "shop-1"}

    def fake_create_sku(products, credential=None, require_live=False):
        assert credential is not None
        assert credential["access_token"] == "printify-token"
        assert require_live is True
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

    def fake_publish_listing(product, credential=None, require_live=False):
        assert credential is not None
        assert credential["access_token"] == "etsy-token"
        assert require_live is True
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
async def test_sku_endpoint_maps_service_credential_error(monkeypatch):
    async def fake_load_oauth_credentials(_user_id, _provider):
        return None

    def fake_create_sku(_products, credential=None, require_live=False):
        raise IntegrationCredentialError("OAuth credentials for printify are required")

    monkeypatch.setattr("services.integration.api.load_oauth_credentials", fake_load_oauth_credentials)
    monkeypatch.setattr("services.integration.api.create_sku", fake_create_sku)

    transport = ASGITransport(app=integration_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/sku",
            headers={"X-User-Id": "42"},
            json={"products": [{"title": "Test", "image_url": "https://example.com/image.png"}]},
        )

    assert response.status_code == 424
    assert "credentials" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_listing_endpoint_maps_service_payload_error(monkeypatch):
    async def fake_load_oauth_credentials(_user_id, _provider):
        return {"access_token": "etsy-token", "account_id": "shop-7"}

    def fake_publish_listing(_product, credential=None, require_live=False):
        raise IntegrationPayloadError("Product payload requires 'image_url'")

    monkeypatch.setattr("services.integration.api.load_oauth_credentials", fake_load_oauth_credentials)
    monkeypatch.setattr("services.integration.api.publish_listing", fake_publish_listing)

    transport = ASGITransport(app=integration_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/listing",
            headers={"X-User-Id": "7"},
            json={"title": "Launch"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_listing_endpoint_maps_service_upstream_error(monkeypatch):
    async def fake_load_oauth_credentials(_user_id, _provider):
        return {"access_token": "etsy-token", "account_id": "shop-7"}

    def fake_publish_listing(_product, credential=None, require_live=False):
        raise IntegrationUpstreamError("Etsy API request failed with status 503: unavailable")

    monkeypatch.setattr("services.integration.api.load_oauth_credentials", fake_load_oauth_credentials)
    monkeypatch.setattr("services.integration.api.publish_listing", fake_publish_listing)

    transport = ASGITransport(app=integration_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/listing",
            headers={"X-User-Id": "7"},
            json={"title": "Launch"},
        )

    assert response.status_code == 502
    assert "status 503" in response.json()["detail"]


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
