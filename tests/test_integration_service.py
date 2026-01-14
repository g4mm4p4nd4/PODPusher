import logging
from importlib import reload

import httpx

from services.integration import service
from packages.integrations import etsy as etsy_mod
from packages.integrations import printify as printify_mod


def _reload_modules():
    reload(printify_mod)
    reload(etsy_mod)
    reload(service)


def test_create_sku_uses_stub_when_no_key(monkeypatch, caplog):
    monkeypatch.delenv("PRINTIFY_API_KEY", raising=False)
    monkeypatch.delenv("PRINTIFY_SHOP_ID", raising=False)
    _reload_modules()
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
    _reload_modules()
    monkeypatch.setattr(printify_mod.httpx, "Client", DummyPrintifyClient)
    products = [{"title": "Test", "image_url": "http://example.com/image.png"}]
    result = service.create_sku(products)
    assert result[0]["sku"] == "sku123"


def test_publish_listing_uses_stub_when_no_key(monkeypatch, caplog):
    monkeypatch.delenv("ETSY_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ETSY_SHOP_ID", raising=False)
    monkeypatch.delenv("ETSY_CLIENT_ID", raising=False)
    _reload_modules()
    caplog.set_level(logging.INFO)
    product = {"title": "Test"}
    result = service.publish_listing(product)
    assert result["etsy_url"].startswith("https://etsy.example/")


def test_publish_listing_calls_api_when_key(monkeypatch):
    monkeypatch.setenv("ETSY_CLIENT_ID", "cid")
    monkeypatch.setenv("ETSY_ACCESS_TOKEN", "token")
    monkeypatch.setenv("ETSY_SHOP_ID", "123")
    _reload_modules()

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
