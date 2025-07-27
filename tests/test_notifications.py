import pytest
from httpx import AsyncClient, ASGITransport

from services.notifications.api import app as notif_app
from services.notifications.service import (
    create_notification,
    mark_read,
    send_monthly_quota_reset,
)
from services.common.database import init_db, get_session
from services.models import User, Notification


@pytest.mark.asyncio
async def test_create_and_read_notification():
    await init_db()
    transport = ASGITransport(app=notif_app)
    async with get_session() as session:
        user = User(id=1)
        session.add(user)
        await session.commit()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/",
            json={"message": "hello"},
            headers={"X-User-Id": "1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "hello"
        resp2 = await client.get("/", headers={"X-User-Id": "1"})
        assert resp2.status_code == 200
        assert len(resp2.json()) == 1


@pytest.mark.asyncio
async def test_mark_read_and_quota_reset():
    await init_db()
    async with get_session() as session:
        user = User(id=1, images_used=5)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    notif = await create_notification(1, "test")
    await mark_read(notif.id)
    async with get_session() as session:
        check = await session.get(Notification, notif.id)
        assert check.read
    await send_monthly_quota_reset()
    async with get_session() as session:
        user = await session.get(User, 1)
        assert user.images_used == 0
