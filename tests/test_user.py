from datetime import datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from services.auth.service import create_session
from services.common.database import get_session, init_db
from services.common.quotas import plan_limit
from services.models import User
from services.user.api import app as user_app


@pytest.mark.asyncio
async def test_user_me_initializes_defaults():
    await init_db()
    async with get_session() as session:
        existing = await session.get(User, 1)
        if existing:
            await session.delete(existing)
            await session.commit()

    transport = ASGITransport(app=user_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/user/me", headers={"X-User-Id": "1"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] == "free"
        assert data["quota_used"] == 0
        assert data["quota_limit"] == plan_limit("free")
        assert set(data.keys()) == {"plan", "quota_used", "quota_limit"}


@pytest.mark.asyncio
async def test_user_me_accepts_bearer_token():
    await init_db()
    token, _ = await create_session(5)
    transport = ASGITransport(app=user_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/user/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] == "free"


@pytest.mark.asyncio
async def test_increment_quota_respects_free_limit():
    await init_db()
    transport = ASGITransport(app=user_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/user/me", json={"count": 5}, headers={"X-User-Id": "2"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["quota_used"] == 5
        assert data["quota_limit"] == plan_limit("free")


@pytest.mark.asyncio
async def test_increment_quota_allows_unlimited_pro():
    await init_db()
    async with get_session() as session:
        user = User(id=3, plan="pro", quota_used=50, quota_limit=100)
        session.add(user)
        await session.commit()

    transport = ASGITransport(app=user_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/user/me", json={"count": 500}, headers={"X-User-Id": "3"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["quota_limit"] is None
        assert data["quota_used"] == 550


@pytest.mark.asyncio
async def test_missing_limit_is_migrated_and_reset():
    await init_db()
    past = datetime.utcnow() - timedelta(days=40)
    async with get_session() as session:
        user = User(
            id=4,
            plan="free",
            quota_used=10,
            quota_limit=None,
            last_reset=past,
        )
        session.add(user)
        await session.commit()

    transport = ASGITransport(app=user_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/user/me", headers={"X-User-Id": "4"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["quota_limit"] == plan_limit("free")
        assert data["quota_used"] == 0
