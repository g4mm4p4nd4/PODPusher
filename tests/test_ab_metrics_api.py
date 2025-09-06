import pytest
from httpx import AsyncClient, ASGITransport

from services.ab_tests.api import app as ab_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_metrics_all_endpoint():
    await init_db()
    transport = ASGITransport(app=ab_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "name": "Test",
            "experiment_type": "image",
            "variants": [{"name": "A", "weight": 1.0}],
        }
        resp = await client.post("/", json=payload)
        vid = resp.json()["variants"][0]["id"]
        await client.post(f"/{vid}/impression")
        await client.post(f"/{vid}/click")
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        metrics = resp.json()
        assert metrics[0]["id"] == vid
        assert metrics[0]["impressions"] == 1
