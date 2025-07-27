import pytest
from httpx import AsyncClient, ASGITransport
from services.ab_test.api import app as ab_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_ab_test_api_flow():
    await init_db()
    transport = ASGITransport(app=ab_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/ab_tests",
            json={
                "title": "T",
                "description": "D",
                "variant_a": "A",
                "variant_b": "B",
            },
        )
        assert resp.status_code == 200
        test_id = resp.json()["id"]
        resp = await client.post(
            f"/api/ab_tests/{test_id}/record_click",
            params={"variant": "A"},
        )
        assert resp.status_code == 200
        resp = await client.get(f"/api/ab_tests/{test_id}")
        data = resp.json()
        assert any(m["clicks"] == 1 for m in data)
