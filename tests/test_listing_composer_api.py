import pytest
from httpx import AsyncClient, ASGITransport

from services.gateway.api import app as gateway_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_listing_draft_crud():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "title": "T",
            "description": "D",
            "tags": ["x"],
            "language": "en",
            "field_order": ["title", "description", "tags"],
        }
        resp = await client.post("/api/listing-composer/drafts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        draft_id = data["id"]

        resp = await client.get(f"/api/listing-composer/drafts/{draft_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "T"

        resp = await client.get("/api/listing-composer/drafts/999")
        assert resp.status_code == 404
