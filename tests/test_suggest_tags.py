import json
import pytest
from httpx import AsyncClient, ASGITransport
from services.ideation.api import app as ideation_app
from services.gateway.api import app as gateway_app


@pytest.mark.asyncio
async def test_suggest_tags_endpoint(monkeypatch):
    async def fake_acreate(**kwargs):
        class R:
            choices = [type('C', (), {'message': type('M', (), {'content': json.dumps(["tag1", "tag2"])})})]
        return R()

    monkeypatch.setenv("OPENAI_API_KEY", "1")
    monkeypatch.setattr("openai.ChatCompletion.acreate", fake_acreate)
    transport = ASGITransport(app=ideation_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/suggest-tags", json={"description": "foo"})
        assert resp.status_code == 200
        assert resp.json() == ["tag1", "tag2"]


@pytest.mark.asyncio
async def test_gateway_suggest_tags():
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/suggest-tags", json={"description": "hello world"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert resp.json()
