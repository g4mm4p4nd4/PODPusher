import asyncio
import importlib


def reload_service(monkeypatch, printify_key=None, etsy_key=None):
    if printify_key is None:
        monkeypatch.delenv("PRINTIFY_API_KEY", raising=False)
    else:
        monkeypatch.setenv("PRINTIFY_API_KEY", printify_key)
    if etsy_key is None:
        monkeypatch.delenv("ETSY_API_KEY", raising=False)
    else:
        monkeypatch.setenv("ETSY_API_KEY", etsy_key)
    monkeypatch.setenv("PRINTIFY_USE_STUB", "1" if printify_key is None else "0")
    monkeypatch.setenv("ETSY_USE_STUB", "1" if etsy_key is None else "0")
    return importlib.reload(importlib.import_module("services.integration.service"))


def test_create_sku_stub(monkeypatch):
    service = reload_service(monkeypatch, printify_key=None)
    result = asyncio.run(service.create_sku([{}]))
    assert result[0]["sku"].startswith("stub-sku")


def test_publish_listing_stub(monkeypatch):
    service = reload_service(monkeypatch, etsy_key=None)
    result = asyncio.run(service.publish_listing({}))
    assert result["etsy_url"].startswith("http://")


def test_create_sku_delegate(monkeypatch):
    service = reload_service(monkeypatch, printify_key="x")

    class Dummy:
        async def create_skus(self, products):
            return ["real-sku"]

    service.printify_client = Dummy()
    result = asyncio.run(service.create_sku([{}]))
    assert result[0]["sku"] == "real-sku"


def test_publish_listing_delegate(monkeypatch):
    service = reload_service(monkeypatch, etsy_key="x")

    class Dummy:
        async def publish_listing(self, product):
            return "http://etsy.com/real"

    service.etsy_client = Dummy()
    result = asyncio.run(service.publish_listing({}))
    assert result["etsy_url"] == "http://etsy.com/real"
