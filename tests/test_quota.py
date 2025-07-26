import pytest
from httpx import AsyncClient, ASGITransport
from services.image_gen.api import app as image_app
from services.user.api import app as user_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_user_plan_endpoint():
    await init_db()
    transport = ASGITransport(app=user_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/user/plan", headers={"X-User-Id": "1"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] == "free"
        assert data["limit"] == 20
        assert data["images_used"] == 0


@pytest.mark.asyncio
async def test_image_quota_enforced():
    await init_db()
    transport = ASGITransport(app=image_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(2):
            resp = await client.post(
                "/images",
                json={"ideas": ["a"] * 10},
                headers={"X-User-Id": "1"},
            )
            assert resp.status_code == 200
        resp = await client.post(
            "/images",
            json={"ideas": ["a"]},
            headers={"X-User-Id": "1"},
        )
        assert resp.status_code == 402
