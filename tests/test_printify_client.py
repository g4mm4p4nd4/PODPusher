import json
from pathlib import Path

import httpx
import pytest

from packages.integrations.printify import PrintifyClient, PrintifyStubClient

FIXTURES = Path(__file__).parent / "integrations" / "fixtures"


@pytest.mark.asyncio
async def test_printify_stub():
    client = PrintifyStubClient()
    skus = await client.create_skus([{"title": "t"}])
    assert skus == ["stub-sku-1"]


@pytest.mark.asyncio
async def test_printify_client(monkeypatch):
    data = json.loads((FIXTURES / "printify_create_sku.json").read_text())

    async def handler(request):
        assert request.headers["Authorization"].startswith("Bearer")
        return httpx.Response(200, json=data)

    transport = httpx.MockTransport(handler)
    original = httpx.AsyncClient

    def mock_async_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", mock_async_client)
    client = PrintifyClient("token", shop_id="1")
    skus = await client.create_skus([{"title": "p"}])
    assert skus == [data["sku"]]
