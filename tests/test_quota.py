import pytest
from httpx import AsyncClient, ASGITransport

from services.auth.service import create_session
from services.common.database import get_session, init_db
from services.image_gen.api import app as image_app
from services.models import Idea, Trend, User


async def _seed_idea() -> int:
    async with get_session() as session:
        trend = Trend(term="cat", category="animals")
        session.add(trend)
        await session.commit()
        await session.refresh(trend)

        idea = Idea(trend_id=trend.id, description="cat t-shirt")
        session.add(idea)
        await session.commit()
        await session.refresh(idea)
        return int(idea.id)


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


@pytest.mark.asyncio
async def test_quota_accepts_bearer_session_without_user_header():
    await init_db()
    async with get_session() as session:
        existing = await session.get(User, 31)
        if existing:
            await session.delete(existing)
            await session.commit()
    token, _ = await create_session(31)

    transport = ASGITransport(app=image_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for i in range(21):
            resp = await client.post(
                "/images",
                json={"ideas": ["idea"]},
                headers={"Authorization": f"Bearer {token}"},
            )
            if i < 20:
                assert resp.status_code == 200
            else:
                assert resp.status_code == 403


@pytest.mark.asyncio
async def test_quota_rejects_invalid_user_header():
    await init_db()
    transport = ASGITransport(app=image_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/images",
            json={"ideas": ["idea"]},
            headers={"X-User-Id": "not-a-number"},
        )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid X-User-Id header"


@pytest.mark.asyncio
async def test_quota_rejects_missing_auth_identity():
    await init_db()
    transport = ASGITransport(app=image_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/images",
            json={"ideas": ["idea"]},
        )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Authentication required"


@pytest.mark.asyncio
async def test_quota_rejects_invalid_bearer_even_with_user_header():
    await init_db()
    transport = ASGITransport(app=image_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/images",
            json={"ideas": ["idea"]},
            headers={
                "Authorization": "Bearer invalid-token",
                "X-User-Id": "44",
            },
        )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Authentication required"


@pytest.mark.asyncio
async def test_quota_rejects_malformed_authorization_header():
    await init_db()
    transport = ASGITransport(app=image_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/images",
            json={"ideas": ["idea"]},
            headers={
                "Authorization": "Token abc123",
                "X-User-Id": "44",
            },
        )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid Authorization header"


@pytest.mark.asyncio
async def test_quota_enforcement_on_generate_endpoint():
    await init_db()
    idea_id = await _seed_idea()
    async with get_session() as session:
        existing = await session.get(User, 77)
        if existing:
            await session.delete(existing)
            await session.commit()

    transport = ASGITransport(app=image_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for i in range(21):
            resp = await client.post(
                "/generate",
                json={"idea_id": idea_id, "style": "default", "provider_override": "stub"},
                headers={"X-User-Id": "77"},
            )
            if i < 20:
                assert resp.status_code == 200
            else:
                assert resp.status_code == 403
