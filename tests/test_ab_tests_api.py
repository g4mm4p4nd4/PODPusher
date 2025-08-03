import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from services.ab_tests.api import app as ab_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_ab_tests_api():
    await init_db()
    test_app = FastAPI()
    test_app.mount("/api/ab-tests", ab_app)
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/ab-tests/",
            json={
                "name": "Test",
                "variants": [
                    {
                        "listing_id": 1,
                        "title": "A",
                        "description": "Desc",
                    }
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        vid = data["variants"][0]["id"]
        resp = await client.post(f"/api/ab-tests/{vid}/impression")
        assert resp.status_code == 200
        resp = await client.post(f"/api/ab-tests/{vid}/click")
        assert resp.status_code == 200
        resp = await client.get(f"/api/ab-tests/{data['id']}/metrics")
        assert resp.status_code == 200
        metrics = resp.json()
        assert len(metrics) == 1
        assert metrics[0]["clicks"] == 1
