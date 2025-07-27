import pytest
from httpx import AsyncClient, ASGITransport
from services.user.api import app as user_app
from services.common.database import init_db, get_session
from services.common.quotas import PLAN_LIMITS
from services.models import User


@pytest.mark.asyncio
async def test_user_plan_endpoint():
    await init_db()
    async with get_session() as session:
        existing = await session.get(User, 1)
        if existing:
            await session.delete(existing)
            await session.commit()
    transport = ASGITransport(app=user_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/user/plan", headers={"X-User-Id": "1"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] == "free"
        assert data["images_used"] == 0
        assert data["limit"] == PLAN_LIMITS["free"]
        assert set(data.keys()) == {"plan", "images_used", "limit"}
