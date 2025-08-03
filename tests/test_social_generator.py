import asyncio
from fastapi.testclient import TestClient

from services.social_generator.api import app
from services.social_generator.service import generate_post

client = TestClient(app)


def test_generate_post_api(monkeypatch):
    monkeypatch.setenv("OPENAI_USE_STUB", "1")
    resp = client.post("/social/post", json={"prompt": "hello"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["caption"].startswith("Caption for: hello")
    assert data["image_url"].startswith("http")


def test_generate_post_service(monkeypatch):
    monkeypatch.setenv("OPENAI_USE_STUB", "1")
    result = asyncio.run(generate_post("hi"))
    assert result["caption"].startswith("Caption for: hi")
