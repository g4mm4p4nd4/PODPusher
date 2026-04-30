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
            "niche": "Dog Lovers",
            "primary_keyword": "dog mom",
            "market_evidence": {
                "title": "Dog Mom Shirt Bestseller",
                "source": "amazon",
                "source_url": "https://example.com/dog-mom-shirt",
                "image_url": "https://example.com/dog-mom-shirt.jpg",
                "provenance": {
                    "source": "amazon",
                    "is_estimated": False,
                    "updated_at": "2026-04-30T00:00:00",
                    "confidence": 0.78,
                },
            },
        }
        resp = await client.post("/api/listing-composer/drafts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        draft_id = data["id"]
        assert data["revision_count"] == 1
        assert data["provenance"]["source"] == "listingdraft_table"

        resp = await client.get(f"/api/listing-composer/drafts/{draft_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "T"
        assert body["niche"] == "Dog Lovers"
        assert body["market_evidence"]["title"] == "Dog Mom Shirt Bestseller"

        list_resp = await client.get("/api/listing-composer/drafts")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 1

        history = await client.get(f"/api/listing-composer/drafts/{draft_id}/history")
        assert history.status_code == 200
        assert history.json()[0]["metadata"]["primary_keyword"] == "dog mom"
        assert history.json()[0]["metadata"]["market_evidence"]["source"] == "amazon"

        resp = await client.get("/api/listing-composer/drafts/999")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_publish_queue_marks_live_publish_as_implementation_required():
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
        assert body["mode"] == "implementation_required"
        assert body["integration_status"]["etsy"]["status"] == "needs_implementation"
        assert body["integration_status"]["etsy"]["blocking"] is False
        assert body["provenance"]["source"] == "automationjob_table"

        queue = await client.get("/api/listing-composer/publish-queue")
        assert queue.status_code == 200
        assert queue.json()["items"][0]["draft_id"] == draft_id
        assert queue.json()["items"][0]["provenance"]["source"] == "automationjob_table"


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
        assert body["metadata"]["revision_count"] == 1
        assert (
            body["metadata"]["latest_revision_provenance"]["source"]
            == "listingdraftrevision_table"
        )
        assert (
            body["metadata"]["integration_contract"]["etsy"]
            == "needs_live_publish_implementation_or_credentials"
        )
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


@pytest.mark.asyncio
async def test_drafts_and_publish_queue_clamp_pagination_and_filter_status():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        draft_ids: list[int] = []
        for index in range(3):
            draft_resp = await client.post(
                "/api/listing-composer/drafts",
                json={
                    "title": f"Paged Draft {index}",
                    "description": "Local persisted composer draft.",
                    "tags": ["paged"],
                    "language": "en",
                    "field_order": ["title", "description", "tags"],
                },
            )
            assert draft_resp.status_code == 200
            draft_ids.append(draft_resp.json()["id"])

        drafts = await client.get(
            "/api/listing-composer/drafts?page=99&page_size=2&sort_by=title&sort_order=asc"
        )
        assert drafts.status_code == 200
        drafts_body = drafts.json()
        assert drafts_body["total"] == 3
        assert drafts_body["page"] == 2
        assert drafts_body["page_size"] == 2
        assert drafts_body["sort_by"] == "title"
        assert drafts_body["sort_order"] == "asc"
        assert drafts_body["items"][0]["provenance"]["source"] == "listingdraft_table"

        for draft_id in draft_ids:
            queue_resp = await client.post(
                f"/api/listing-composer/drafts/{draft_id}/publish-queue"
            )
            assert queue_resp.status_code == 200

        empty_status = await client.get(
            "/api/listing-composer/publish-queue?status=failed&page=3&page_size=2"
        )
        assert empty_status.status_code == 200
        assert empty_status.json()["page"] == 1
        assert empty_status.json()["items"] == []

        pending = await client.get(
            "/api/listing-composer/publish-queue?status=pending&page=99&page_size=2"
        )
        assert pending.status_code == 200
        pending_body = pending.json()
        assert pending_body["total"] == 3
        assert pending_body["page"] == 2
        assert pending_body["items"][0]["status"] == "pending"
        assert pending_body["items"][0]["provenance"]["source"] == "automationjob_table"
