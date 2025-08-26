import logging
from importlib import reload

import httpx

from services.integration import service
from packages.integrations import printify as printify_mod
from packages.integrations import etsy as etsy_mod


def _reload_modules():
    reload(printify_mod)
    reload(etsy_mod)
    reload(service)


def test_create_sku_uses_stub_when_no_key(monkeypatch, caplog):
    monkeypatch.delenv("PRINTIFY_API_KEY", raising=False)
    _reload_modules()
    caplog.set_level(logging.INFO)
    products = [{"title": "Test"}]
    result = service.create_sku(products)
    assert result[0]["sku"].startswith("stub-sku-")
    assert "PRINTIFY_API_KEY missing" in caplog.text


def test_create_sku_calls_api_when_key(monkeypatch):
    monkeypatch.setenv("PRINTIFY_API_KEY", "real")
    _reload_modules()

    def fake_post(url, json, headers, timeout):
        assert headers["Authorization"] == "Bearer real"
        return httpx.Response(
            200, json={"id": "sku123"}, request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(printify_mod.httpx, "post", fake_post)
    products = [{"title": "Test"}]
    result = service.create_sku(products)
    assert result[0]["sku"] == "sku123"


def test_publish_listing_uses_stub_when_no_key(monkeypatch, caplog):
    monkeypatch.delenv("ETSY_API_KEY", raising=False)
    _reload_modules()
    caplog.set_level(logging.INFO)
    product = {"title": "Test"}
    result = service.publish_listing(product)
    assert result["etsy_url"].startswith("http://etsy.example/listing")
    assert "ETSY_API_KEY missing" in caplog.text


def test_publish_listing_calls_api_when_key(monkeypatch):
    monkeypatch.setenv("ETSY_API_KEY", "key")
    _reload_modules()

    def fake_post(url, json, headers, timeout):
        assert headers["x-api-key"] == "key"
        return httpx.Response(
            200,
            json={"url": "http://etsy.com/listing/1"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(etsy_mod.httpx, "post", fake_post)
    product = {"title": "Test"}
    result = service.publish_listing(product)
    assert result["etsy_url"] == "http://etsy.com/listing/1"
    assert result["listing_url"] == "http://etsy.com/listing/1"
