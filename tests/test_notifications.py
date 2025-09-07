import pytest
from httpx import ASGITransport, AsyncClient

from services.notifications.api import app as notif_app
from services.notifications.service import get_service
from services.common.database import get_session, init_db
from services.models import User


@pytest.mark.asyncio
async def test_schedule_and_mark_read():
    await init_db()
    service = get_service()
    transport = ASGITransport(app=notif_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/notifications/schedule",
            json={
                "type": "scheduled_post",
                "message": "hello",
                "delivery_method": "in_app",
            },
            headers={"X-User-Id": "1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"

        # send scheduled notifications
        await service.send_due_notifications()

        resp = await client.get(
            "/api/notifications", headers={"X-User-Id": "1"}
        )
        items = resp.json()
        assert items[0]["status"] == "sent"

        resp = await client.post(
            "/api/notifications/mark_read",
            json={"id": data["id"]},
            headers={"X-User-Id": "1"},
        )
        assert resp.json()["read"] is True

        pref_resp = await client.post(
            "/api/notifications/preferences",
            json={"type": "trending_product", "delivery_method": "email"},
            headers={"X-User-Id": "1"},
        )
        assert pref_resp.json()["delivery_method"] == "email"


@pytest.mark.asyncio
async def test_scheduler_jobs(monkeypatch):
    await init_db()
    async with get_session() as session:
        user = User(id=1, quota_used=5)
        session.add(user)
        await session.commit()

    service = get_service()

    async def fake_fetch_trends():
        return [{"term": "foo", "category": "general"}]

    monkeypatch.setattr(
        "services.notifications.service.fetch_trends", fake_fetch_trends
    )

    await service.reset_monthly_quotas()
    async with get_session() as session:
        user = await session.get(User, 1)
        assert user.quota_used == 0

    await service.check_trending_products()
    transport = ASGITransport(app=notif_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/notifications", headers={"X-User-Id": "1"}
        )
        messages = [n["type"] for n in resp.json()]
        assert "quota_reset" in messages
        assert "trending_product" in messages
