import pytest
from httpx import AsyncClient, ASGITransport

from services.notifications.api import app as notif_app
from services.notifications.service import reset_monthly_quotas, weekly_trending_summary
from services.common.database import init_db, get_session
from services.models import User


@pytest.mark.asyncio
async def test_notification_crud():
    await init_db()
    transport = ASGITransport(app=notif_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/", json={"message": "hello", "type": "info"}, headers={"X-User-Id": "1"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "hello"
        assert data["type"] == "info"

        resp = await client.get("/", headers={"X-User-Id": "1"})
        assert resp.status_code == 200
        notifs = resp.json()
        assert len(notifs) == 1
        assert notifs[0]["read_status"] is False

        resp = await client.put(f"/{data['id']}/read")
        assert resp.status_code == 200
        assert resp.json()["read_status"] is True


@pytest.mark.asyncio
async def test_scheduler_jobs(monkeypatch):
    await init_db()
    async with get_session() as session:
        user = User(id=1, quota_used=5)
        session.add(user)
        await session.commit()

    async def fake_fetch_trends(category=None):
        return [{"term": "foo", "category": "general"}]

    monkeypatch.setattr("services.notifications.service.fetch_trends", fake_fetch_trends)

    await reset_monthly_quotas()
    async with get_session() as session:
        user = await session.get(User, 1)
        assert user.quota_used == 0

    await weekly_trending_summary()
    transport = ASGITransport(app=notif_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/", headers={"X-User-Id": "1"})
        messages = [n["message"] for n in resp.json()]
        assert any("Weekly trending" in m for m in messages)
        assert any("quota" in m for m in messages)
