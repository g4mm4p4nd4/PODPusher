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


@pytest.mark.asyncio
async def test_publish_queue_creates_demo_job_and_retains_draft_id():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "title": "Boho Sun Wall Art",
            "description": "Warm wall art for home decor buyers.",
            "tags": ["boho", "sun"],
            "language": "en",
            "field_order": ["title", "description", "tags"],
        }
        draft_resp = await client.post("/api/listing-composer/drafts", json=payload)
        assert draft_resp.status_code == 200
        draft_id = draft_resp.json()["id"]

        resp = await client.post(
            f"/api/listing-composer/drafts/{draft_id}/publish-queue"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["draft_id"] == draft_id
        assert body["queue_item_id"] > 0
        assert body["status"] == "pending"
        assert body["mode"] == "demo"
        assert body["integration_status"]["etsy"]["status"] == "demo"


@pytest.mark.asyncio
async def test_publish_queue_missing_draft_returns_404():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/listing-composer/drafts/404/publish-queue")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_export_payload_shape_for_json_and_csv():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "title": "Boho Sun Wall Art",
            "description": "Warm wall art for home decor buyers.",
            "tags": ["boho", "sun"],
            "language": "en",
            "field_order": ["title", "description", "tags"],
        }
        draft_resp = await client.post("/api/listing-composer/drafts", json=payload)
        draft_id = draft_resp.json()["id"]

        resp = await client.get(f"/api/listing-composer/drafts/{draft_id}/export")
        assert resp.status_code == 200
        assert "attachment" in resp.headers["content-disposition"]
        body = resp.json()
        assert body["draft_id"] == draft_id
        assert body["title"] == payload["title"]
        assert body["description"] == payload["description"]
        assert body["tags"] == payload["tags"]
        assert body["metadata"]["language"] == "en"
        assert "optimization_score" in body["score"]
        assert "status" in body["compliance"]
        assert body["provenance"]["source"] == "local_estimator"
        assert body["provenance"]["export_status"] == "ready"

        csv_resp = await client.get(
            f"/api/listing-composer/drafts/{draft_id}/export?format=csv"
        )
        assert csv_resp.status_code == 200
        assert csv_resp.headers["content-type"].startswith("text/csv")
        assert "draft_id,title,description,tags" in csv_resp.text
