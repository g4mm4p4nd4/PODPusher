import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from services.ab_tests.api import app as ab_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_ab_tests_api():
    await init_db()
    transport = ASGITransport(app=ab_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "name": "Test",
            "experiment_type": "image",
            "variants": [{"name": "A", "weight": 1.0}],
        }
        resp = await client.post("/", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        vid = data["variants"][0]["id"]
        resp = await client.post(f"/{vid}/impression")
        assert resp.status_code == 200
        resp = await client.post(f"/{vid}/click")
        assert resp.status_code == 200
        resp = await client.get(f"/{data['id']}/metrics")
        assert resp.status_code == 200
        metrics = resp.json()
        assert metrics[0]["weight"] == 1.0


@pytest.mark.asyncio
async def test_api_weight_validation_and_schedule():
    await init_db()
    transport = ASGITransport(app=ab_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        bad = {
            "name": "Bad",
            "experiment_type": "price",
            "variants": [{"name": "A", "weight": 0.6}, {"name": "B", "weight": 0.5}],
        }
        resp = await client.post("/", json=bad)
        assert resp.status_code == 400
        future = (datetime.utcnow() + timedelta(days=1)).isoformat()
        payload = {
            "name": "Sched",
            "experiment_type": "description",
            "start_time": future,
            "variants": [{"name": "A", "weight": 1.0}],
        }
        resp = await client.post("/", json=payload)
        data = resp.json()
        vid = data["variants"][0]["id"]
        resp = await client.post(f"/{vid}/impression")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_api_create_filters_and_actions():
    await init_db()
    transport = ASGITransport(app=ab_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "name": "Retro Sunset Title",
            "product_id": 101,
            "experiment_type": "title",
            "variants": [
                {"name": "Title A", "weight": 0.5},
                {"name": "Title B", "weight": 0.5},
            ],
        }
        created = await client.post("/", json=payload)
        assert created.status_code == 200
        body = created.json()
        assert body["product"] == "Retro Beach Sunset Tee"
        assert body["integration_status"]["listing_push"] == "local_state"

        dashboard = await client.get(
            "/dashboard", params={"search": "sunset", "status": "running"}
        )
        assert dashboard.status_code == 200
        experiments = dashboard.json()["experiments"]
        assert [item["id"] for item in experiments] == [body["id"]]
        assert experiments[0]["actions_available"] == [
            "pause",
            "duplicate",
            "end",
            "push-winner",
        ]

        paused = await client.post(f"/{body['id']}/pause")
        assert paused.status_code == 200
        assert paused.json()["status"] == "paused"

        duplicated = await client.post(f"/{body['id']}/duplicate")
        assert duplicated.status_code == 200
        assert duplicated.json()["name"] == "Retro Sunset Title Copy"

        ended = await client.post(f"/{body['id']}/end")
        assert ended.status_code == 200
        assert ended.json()["status"] == "completed"

        pushed = await client.post(f"/{body['id']}/push-winner")
        assert pushed.status_code == 200
        assert pushed.json()["status"] == "pushed"


@pytest.mark.asyncio
async def test_api_demo_winner_metadata():
    await init_db()
    transport = ASGITransport(app=ab_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        pushed = await client.post("/0/push-winner")
        assert pushed.status_code == 200
        assert pushed.json()["demo_state"] is True
