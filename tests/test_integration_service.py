import logging

import httpx
import pytest

from services.integration import service
from packages.integrations import etsy as etsy_mod
from packages.integrations import printify as printify_mod


def test_create_sku_uses_stub_when_no_key(monkeypatch, caplog):
    monkeypatch.delenv("PRINTIFY_API_KEY", raising=False)
    monkeypatch.delenv("PRINTIFY_SHOP_ID", raising=False)
    caplog.set_level(logging.INFO)
    products = [{"title": "Test", "image_url": "http://example.com/image.png"}]
    result = service.create_sku(products)
    assert result[0]["sku"].startswith("stub-sku-")
    assert "Printify credentials missing" in caplog.text


class DummyPrintifyClient:
    def __init__(self, *args, **kwargs):
        self.last = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, json, headers, timeout=None):
        assert headers["Authorization"] == "Bearer real"
        assert "shops/shop-1/products.json" in url
        self.last = {"url": url, "payload": json}
        return httpx.Response(200, json={"id": "sku123"}, request=httpx.Request("POST", url))


def test_create_sku_calls_api_when_key(monkeypatch):
    monkeypatch.setenv("PRINTIFY_API_KEY", "real")
    monkeypatch.setenv("PRINTIFY_SHOP_ID", "shop-1")
    monkeypatch.setattr(printify_mod.httpx, "Client", DummyPrintifyClient)
    products = [{"title": "Test", "image_url": "http://example.com/image.png"}]
    result = service.create_sku(products)
    assert result[0]["sku"] == "sku123"


def test_publish_listing_uses_stub_when_no_key(monkeypatch, caplog):
    monkeypatch.delenv("ETSY_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ETSY_SHOP_ID", raising=False)
    monkeypatch.delenv("ETSY_CLIENT_ID", raising=False)
    caplog.set_level(logging.INFO)
    product = {"title": "Test"}
    result = service.publish_listing(product)
    assert result["etsy_url"].startswith("https://etsy.example/")


def test_publish_listing_calls_api_when_key(monkeypatch):
    monkeypatch.setenv("ETSY_CLIENT_ID", "cid")
    monkeypatch.setenv("ETSY_ACCESS_TOKEN", "token")
    monkeypatch.setenv("ETSY_SHOP_ID", "123")

    def fake_post(url, json, headers, timeout):
        assert headers["x-api-key"] == "cid"
        assert headers["Authorization"] == "Bearer token"
        return httpx.Response(
            200,
            json={"listing_id": 1, "url": "http://etsy.com/listing/1"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(etsy_mod.httpx, "post", fake_post)
    product = {"title": "Test"}
    result = service.publish_listing(product)
    assert result["etsy_url"] == "http://etsy.com/listing/1"
    assert result["listing_url"] == "http://etsy.com/listing/1"


def test_create_sku_require_live_requires_oauth_credential():
    with pytest.raises(service.IntegrationCredentialError):
        service.create_sku([{"title": "Test"}], credential=None, require_live=True)


def test_publish_listing_require_live_requires_etsy_client_id(monkeypatch):
    monkeypatch.delenv("ETSY_CLIENT_ID", raising=False)
    with pytest.raises(service.IntegrationCredentialError):
        service.publish_listing(
            {"title": "Test"},
            credential={"access_token": "token", "account_id": "shop-1"},
            require_live=True,
        )


def test_create_sku_maps_payload_and_upstream_errors(monkeypatch):
    def payload_error(_products):
        raise ValueError("bad payload")

    def upstream_error(_products):
        raise httpx.ReadTimeout("timeout")

    monkeypatch.setattr(service, "get_printify_client", lambda *_: payload_error)
    with pytest.raises(service.IntegrationPayloadError):
        service.create_sku([{"title": "Test"}], credential={"access_token": "x", "account_id": "y"})

    monkeypatch.setattr(service, "get_printify_client", lambda *_: upstream_error)
    with pytest.raises(service.IntegrationUpstreamError):
        service.create_sku([{"title": "Test"}], credential={"access_token": "x", "account_id": "y"})


def test_create_sku_maps_runtime_upstream_error(monkeypatch):
    def upstream_runtime(_products):
        raise RuntimeError("Printify API request failed with status 429: rate limit")

    monkeypatch.setattr(service, "get_printify_client", lambda *_: upstream_runtime)
    with pytest.raises(service.IntegrationUpstreamError, match="status 429"):
        service.create_sku([{"title": "Test"}], credential={"access_token": "x", "account_id": "y"})


def test_publish_listing_maps_runtime_upstream_error(monkeypatch):
    def upstream_runtime(_product):
        raise RuntimeError("Etsy API transport error: ConnectTimeout")

    monkeypatch.setattr(service, "get_etsy_client", lambda *_: upstream_runtime)
    with pytest.raises(service.IntegrationUpstreamError, match="ConnectTimeout"):
        service.publish_listing(
            {"title": "Test"},
            credential={"access_token": "x", "account_id": "y"},
            require_live=False,
        )
