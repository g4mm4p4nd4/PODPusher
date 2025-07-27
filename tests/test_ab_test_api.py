import pytest
from httpx import AsyncClient, ASGITransport
from services.gateway.api import app as gateway_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_ab_test_api_flow():
    await init_db()
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/ab_tests/",
            json={
                "variant_a": {"title": "A", "description": "", "tags": []},
                "variant_b": {"title": "B", "description": "", "tags": []},
            },
        )
        assert resp.status_code == 200
        test_id = resp.json()["id"]
        await client.post(
            f"/api/ab_tests/{test_id}/record_click", json={"variant": "A"}
        )
        resp2 = await client.get(f"/api/ab_tests/{test_id}")
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["id"] == test_id
        assert len(data["variants"]) == 2
