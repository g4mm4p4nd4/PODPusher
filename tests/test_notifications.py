import pytest
from datetime import datetime, timedelta
from httpx import ASGITransport, AsyncClient
from sqlmodel import select

from services.auth.service import create_session
from services.common.database import get_session, init_db
from services.models import Notification, ScheduledNotification, User
from services.notifications.api import app as notif_app
from services.notifications.service import (
    dispatch_due_notifications,
    list_scheduled_notifications,
    reset_monthly_quotas,
    schedule_notification,
    weekly_trending_summary,
)


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

        resp = await client.put(f"/{data['id']}/read", headers={"X-User-Id": "1"})
        assert resp.status_code == 200
        assert resp.json()["read_status"] is True


@pytest.mark.asyncio
async def test_mark_read_denies_other_user():
    await init_db()
    transport = _transport()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/",
            json={"message": "private", "type": "info"},
            headers={"X-User-Id": "11"},
        )
        notification_id = create_resp.json()["id"]

        denied_resp = await client.put(
            f"/{notification_id}/read",
            headers={"X-User-Id": "12"},
        )
        assert denied_resp.status_code == 404

        owner_list_resp = await client.get("/", headers={"X-User-Id": "11"})
        owner_notifications = owner_list_resp.json()
        assert owner_notifications[0]["read_status"] is False


@pytest.mark.asyncio
async def test_invalid_user_header_returns_400():
    await init_db()
    transport = _transport()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_resp = await client.get("/", headers={"X-User-Id": "abc"})
        assert list_resp.status_code == 400
        assert list_resp.json()["detail"] == "Invalid X-User-Id header"

        read_resp = await client.put("/1/read", headers={"X-User-Id": "abc"})
        assert read_resp.status_code == 400
        assert read_resp.json()["detail"] == "Invalid X-User-Id header"


@pytest.mark.asyncio
async def test_notification_endpoints_accept_bearer_session():
    await init_db()
    token, _ = await create_session(21)
    transport = _transport()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/",
            json={"message": "bearer hello", "type": "info"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_resp.status_code == 200
        notification_id = create_resp.json()["id"]

        list_resp = await client.get(
            "/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.status_code == 200
        assert any(item["id"] == notification_id for item in list_resp.json())

        mark_resp = await client.put(
            f"/{notification_id}/read",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert mark_resp.status_code == 200
        assert mark_resp.json()["read_status"] is True


@pytest.mark.asyncio
async def test_notification_endpoints_reject_invalid_bearer_session():
    await init_db()
    transport = _transport()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Authentication required"


@pytest.mark.asyncio
async def test_notification_endpoints_reject_malformed_authorization_header():
    await init_db()
    transport = _transport()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/",
            headers={"Authorization": "Token invalid", "X-User-Id": "1"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Authentication required"


@pytest.mark.asyncio
async def test_notification_endpoints_reject_payload_user_id_override():
    await init_db()
    transport = _transport()
    schedule_time = datetime.utcnow() + timedelta(minutes=5)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/",
            json={"message": "hello", "type": "info", "user_id": 99},
            headers={"X-User-Id": "1"},
        )
        assert create_resp.status_code == 422

        scheduled_resp = await client.post(
            "/scheduled",
            json={
                "message": "Launch teaser",
                "type": "launch",
                "scheduled_for": schedule_time.isoformat(),
                "user_id": 99,
            },
            headers={"X-User-Id": "1"},
        )
        assert scheduled_resp.status_code == 422


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
async def test_scheduled_cancel_denies_other_user():
    await init_db()
    transport = _transport()
    schedule_time = datetime.utcnow() + timedelta(minutes=10)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/scheduled",
            json={
                "message": "Owner only",
                "type": "launch",
                "scheduled_for": schedule_time.isoformat(),
            },
            headers={"X-User-Id": "10"},
        )
        job_id = create_resp.json()["id"]

        denied_resp = await client.delete(
            f"/scheduled/{job_id}",
            headers={"X-User-Id": "11"},
        )
        assert denied_resp.status_code == 404


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
