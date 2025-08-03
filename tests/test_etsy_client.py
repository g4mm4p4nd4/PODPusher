import json
from pathlib import Path

import httpx
import pytest

from packages.integrations.etsy import EtsyClient, EtsyStubClient

FIXTURES = Path(__file__).parent / "integrations" / "fixtures"


@pytest.mark.asyncio
async def test_etsy_stub():
    client = EtsyStubClient()
    url = await client.publish_listing({"title": "t"})
    assert url.startswith("http://")


@pytest.mark.asyncio
async def test_etsy_client(monkeypatch):
    data = json.loads((FIXTURES / "etsy_publish_listing.json").read_text())

    async def handler(request):
        assert request.headers["x-api-key"] == "token"
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    def mock_async_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", mock_async_client)
    client = EtsyClient("token")
    url = await client.publish_listing({"title": "p"})
    assert url == data["url"]
