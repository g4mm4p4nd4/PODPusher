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
