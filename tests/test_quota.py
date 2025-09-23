import pytest
from httpx import AsyncClient, ASGITransport

from services.common.database import get_session, init_db
from services.image_gen.api import app as image_app
from services.models import User


@pytest.mark.asyncio
async def test_quota_enforcement():
    await init_db()
    async with get_session() as session:
        existing = await session.get(User, 1)
        if existing:
            await session.delete(existing)
            await session.commit()
    transport = ASGITransport(app=image_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for i in range(21):
            resp = await client.post(
                "/images",
                json={"ideas": ["idea"]},
                headers={"X-User-Id": "1"},
            )
            if i < 20:
                assert resp.status_code == 200
            else:
                assert resp.status_code == 403


@pytest.mark.asyncio
async def test_quota_allows_pro_users():
    await init_db()
    async with get_session() as session:
        user = User(id=2, plan="pro", quota_used=95, quota_limit=100)
        session.add(user)
        await session.commit()

    transport = ASGITransport(app=image_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(25):
            resp = await client.post(
                "/images",
                json={"ideas": ["idea"]},
                headers={"X-User-Id": "2"},
            )
            assert resp.status_code == 200
