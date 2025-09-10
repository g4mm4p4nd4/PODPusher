import logging
from importlib import reload

import httpx
import pytest

from services.integration import service
from packages.integrations import printify as printify_mod
from packages.integrations import etsy as etsy_mod
from packages.integrations import gemini as gemini_mod


def _reload_modules():
    reload(printify_mod)
    reload(etsy_mod)
    reload(service)


@pytest.fixture
def mock_gemini(monkeypatch):
    calls = []

    def fake_generate(prompt: str) -> str:
        calls.append(prompt)
        return f"http://mock/{len(calls)}.png"

    monkeypatch.setattr(gemini_mod, "generate_mockup", fake_generate)
    return calls


def test_create_printify_product(monkeypatch, mock_gemini):
    monkeypatch.setenv("PRINTIFY_API_KEY", "key")
    _reload_modules()

    def fake_post(url, json, headers, timeout):
        assert headers["Authorization"] == "Bearer key"
        return httpx.Response(
            200,
            json={"id": "prod1", "variants": [{"id": "v1"}, {"id": "v2"}]},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(printify_mod.httpx, "post", fake_post)
    result = service.create_printify_product(
        "idea", ["img1"], "bp1", ["v1", "v2"]
    )
    assert result["product_id"] == "prod1"
    assert result["variant_ids"] == ["v1", "v2"]
    assert len(mock_gemini) == 2


def test_create_printify_product_error(monkeypatch, mock_gemini):
    monkeypatch.setenv("PRINTIFY_API_KEY", "key")
    _reload_modules()

    def fake_post(url, json, headers, timeout):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr(printify_mod.httpx, "post", fake_post)
    with pytest.raises(httpx.HTTPError):
        service.create_printify_product("idea", ["img"], "bp", ["v1"])


def test_publish_listing(monkeypatch):
    monkeypatch.setenv("ETSY_API_KEY", "key")
    _reload_modules()

    def fake_post(url, json, headers, timeout):
        return httpx.Response(
            200,
            json={"url": "http://etsy/listing"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(etsy_mod.httpx, "post", fake_post)
    product = {"title": "Test"}
    result = service.publish_listing(product)
    assert result["etsy_url"] == "http://etsy/listing"


def test_publish_listing_error(monkeypatch):
    monkeypatch.setenv("ETSY_API_KEY", "key")
    _reload_modules()

    def fake_post(url, json, headers, timeout):
        raise httpx.HTTPError("err")

    monkeypatch.setattr(etsy_mod.httpx, "post", fake_post)
    with pytest.raises(httpx.HTTPError):
        service.publish_listing({"title": "T"})
