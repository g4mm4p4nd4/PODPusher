import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport

from services.notifications.api import app as notif_app
from services.notifications.service import (
    reset_monthly_quotas,
    weekly_trending_summary,
    schedule_notification,
    dispatch_due_notifications,
    list_scheduled_notifications,
)
from services.common.database import init_db, get_session
from services.models import User, Notification, ScheduledNotification
from sqlmodel import select


@pytest.fixture(autouse=True)
def _stub_delivery(monkeypatch):
    monkeypatch.setattr("packages.integrations.notifications.send_email", lambda *_, **__: None)
    monkeypatch.setattr("packages.integrations.notifications.send_push", lambda *_, **__: None)

def _transport():
    return ASGITransport(app=notif_app)


@pytest.mark.asyncio
async def test_notification_crud():
    await init_db()
    transport = _transport()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/",
            json={"message": "hello", "type": "info"},
            headers={"X-User-Id": "1"},
        )
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
    transport = _transport()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/", headers={"X-User-Id": "1"})
        messages = [n["message"] for n in resp.json()]
        assert any("Weekly trending" in m for m in messages)
        assert any("quota" in m for m in messages)


@pytest.mark.asyncio
async def test_scheduled_notification_api():
    await init_db()
    transport = _transport()
    schedule_time = datetime.utcnow() + timedelta(minutes=10)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/scheduled",
            json={
                "message": "Launch teaser",
                "type": "launch",
                "scheduled_for": schedule_time.isoformat(),
                "metadata": {"listing_id": 42},
            },
            headers={"X-User-Id": "1"},
        )
        assert resp.status_code == 200
        created = resp.json()
        assert created["status"] == "pending"
        job_id = created["id"]

        resp = await client.get("/scheduled", headers={"X-User-Id": "1"})
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["id"] == job_id

        resp = await client.delete(f"/scheduled/{job_id}", headers={"X-User-Id": "1"})
        assert resp.status_code == 200
        cancelled = resp.json()
        assert cancelled["status"] == "cancelled"

        resp = await client.get("/scheduled", headers={"X-User-Id": "1"})
        assert resp.status_code == 200
        assert resp.json()[0]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_dispatch_due_notifications():
    await init_db()
    due_time = datetime.utcnow() - timedelta(minutes=5)
    await schedule_notification(
        user_id=1,
        message="Launch now",
        notif_type="launch",
        scheduled_for=due_time,
        metadata={"listing_id": 7},
    )

    await dispatch_due_notifications()

    async with get_session() as session:
        notif_result = await session.exec(
            select(Notification).where(Notification.user_id == 1)
        )
        notifications = notif_result.all()
        assert notifications

        job_result = await session.exec(
            select(ScheduledNotification).where(ScheduledNotification.user_id == 1)
        )
        jobs = job_result.all()
        assert jobs
        assert jobs[0].status == "sent"
        assert jobs[0].dispatched_at is not None

    scheduled = await list_scheduled_notifications(1)
    assert scheduled[0]["status"] == "sent"
