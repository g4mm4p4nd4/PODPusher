from __future__ import annotations
from datetime import datetime
import asyncio
from typing import List, Optional

from sqlmodel import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..common.database import get_session
from ..models import Notification, User
from ..trend_scraper.service import fetch_trends
from packages.integrations.notifications import send_email, send_push


def _to_dict(notification: Notification) -> dict:
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "message": notification.message,
        "type": notification.type,
        "created_at": notification.created_at.isoformat(),
        "read_status": notification.read_status,
    }


async def create_notification(user_id: int, message: str, notif_type: str = "info") -> dict:
    async with get_session() as session:
        n = Notification(user_id=user_id, message=message, type=notif_type)
        session.add(n)
        await session.commit()
        await session.refresh(n)
    # send stubs
    send_email(user_id, message, notif_type)
    send_push(user_id, message, notif_type)
    return _to_dict(n)


async def list_notifications(user_id: int) -> List[dict]:
    async with get_session() as session:
        result = await session.exec(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        notifications = result.all()
        return [_to_dict(n) for n in notifications]


async def mark_read(notification_id: int) -> Optional[dict]:
    async with get_session() as session:
        notif = await session.get(Notification, notification_id)
        if not notif:
            return None
        notif.read_status = True
        session.add(notif)
        await session.commit()
        await session.refresh(notif)
        return _to_dict(notif)


async def reset_monthly_quotas() -> None:
    now = datetime.utcnow()
    async with get_session() as session:
        result = await session.exec(select(User))
        users = result.all()
        ids = [u.id for u in users]
        for u in users:
            u.quota_used = 0
            u.last_reset = now
            session.add(u)
        await session.commit()
    for uid in ids:
        await create_notification(uid, "Monthly quota has been reset.", "system")


async def weekly_trending_summary() -> None:
    trends = await fetch_trends()
    summary = ", ".join(t["term"] for t in trends[:3])
    async with get_session() as session:
        result = await session.exec(select(User.id))
        user_ids = result.all()
    for uid in user_ids:
        await create_notification(uid, f"Weekly trending keywords: {summary}", "summary")


scheduler = AsyncIOScheduler()

scheduler.add_job(
    lambda: asyncio.create_task(reset_monthly_quotas()),
    trigger="cron",
    day=1,
    hour=0,
)

scheduler.add_job(
    lambda: asyncio.create_task(weekly_trending_summary()),
    trigger="cron",
    day_of_week="mon",
    hour=0,
)


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()
