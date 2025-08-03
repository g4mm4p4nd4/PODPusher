import pytest
from httpx import AsyncClient, ASGITransport

from services.gateway.api import app as gateway_app
from services.ideation.service import suggest_tags


@pytest.mark.asyncio
async def test_suggest_tags_function():
    tags = suggest_tags("Funny Dog Shirt", "This is a hilarious dog t-shirt")
    assert "funny" in tags
    assert "dog" in tags
    assert len(tags) <= 13


@pytest.mark.asyncio
async def test_suggest_tags_endpoint():
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/suggest-tags",
            json={"title": "Cat Mug", "description": "Cute cat coffee mug"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert "cat" in data
