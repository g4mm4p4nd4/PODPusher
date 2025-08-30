import pytest
from httpx import AsyncClient, ASGITransport
from services.listing_composer.api import app as listing_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_draft_api_flow():
    await init_db()
    transport = ASGITransport(app=listing_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "title": "t",
            "description": "d",
            "tags": ["a"],
            "language": "en",
            "field_order": ["title", "description", "tags"],
        }
        resp = await client.post("/drafts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        draft_id = data["id"]
        resp = await client.get(f"/drafts/{draft_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "t"
        resp = await client.get("/drafts/999")
        assert resp.status_code == 404
