from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import select

from ..common.database import get_session
from ..models import Notification, ScheduledNotification, User
from ..trend_scraper.service import fetch_trends, get_product_suggestions
from packages.integrations.notifications import send_email, send_push

DISPATCH_INTERVAL_MINUTES = max(1, int(os.getenv("NOTIFY_DISPATCH_INTERVAL_MINUTES", "5")))
LAUNCH_DIGEST_HOUR = int(os.getenv("NOTIFY_LAUNCH_DIGEST_HOUR", "13"))


def _to_dict(notification: Notification) -> dict:
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "message": notification.message,
        "type": notification.type,
        "created_at": notification.created_at.isoformat(),
        "read_status": notification.read_status,
    }


def _scheduled_to_dict(job: ScheduledNotification) -> dict:
    return {
        "id": job.id,
        "user_id": job.user_id,
        "message": job.message,
        "type": job.type,
        "scheduled_for": job.scheduled_for.isoformat(),
        "status": job.status,
        "metadata": job.context or {},
        "created_at": job.created_at.isoformat(),
        "dispatched_at": job.dispatched_at.isoformat() if job.dispatched_at else None,
    }


async def create_notification(user_id: int, message: str, notif_type: str = "info") -> dict:
    async with get_session() as session:
        record = Notification(user_id=user_id, message=message, type=notif_type)
        session.add(record)
        await session.commit()
        await session.refresh(record)
    send_email(user_id, message, notif_type)
    send_push(user_id, message, notif_type)
    return _to_dict(record)


async def list_notifications(user_id: int) -> List[dict]:
    async with get_session() as session:
        result = await session.exec(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        notifications = result.all()
    return [_to_dict(item) for item in notifications]


async def mark_read(notification_id: int) -> Optional[dict]:
    async with get_session() as session:
        record = await session.get(Notification, notification_id)
        if not record:
            return None
        record.read_status = True
        session.add(record)
        await session.commit()
        await session.refresh(record)
    return _to_dict(record)


async def schedule_notification(
    user_id: int,
    message: str,
    notif_type: str = "info",
    *,
    scheduled_for: datetime,
    metadata: Dict[str, Any] | None = None,
) -> dict:
    async with get_session() as session:
        job = ScheduledNotification(
            user_id=user_id,
            message=message,
            type=notif_type,
            scheduled_for=scheduled_for,
            context=metadata or None,
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
    return _scheduled_to_dict(job)


async def list_scheduled_notifications(user_id: int) -> List[dict]:
    async with get_session() as session:
        result = await session.exec(
            select(ScheduledNotification)
            .where(ScheduledNotification.user_id == user_id)
            .order_by(ScheduledNotification.scheduled_for.asc())
        )
        jobs = result.all()
    return [_scheduled_to_dict(job) for job in jobs]


async def cancel_scheduled_notification(job_id: int) -> Optional[dict]:
    async with get_session() as session:
        job = await session.get(ScheduledNotification, job_id)
        if not job:
            return None
        if job.status == "pending":
            job.status = "cancelled"
            session.add(job)
            await session.commit()
            await session.refresh(job)
        else:
            await session.refresh(job)
    return _scheduled_to_dict(job)


async def dispatch_due_notifications() -> None:
    now = datetime.utcnow()
    async with get_session() as session:
        result = await session.exec(
            select(ScheduledNotification)
            .where(ScheduledNotification.status == "pending")
            .where(ScheduledNotification.scheduled_for <= now)
        )
        jobs = result.all()
        for job in jobs:
            await create_notification(job.user_id, job.message, job.type)
            job.status = "sent"
            job.dispatched_at = now
            session.add(job)
        if jobs:
            await session.commit()


async def reset_monthly_quotas() -> None:
    now = datetime.utcnow()
    async with get_session() as session:
        result = await session.exec(select(User))
        users = result.all()
        ids = [item.id for item in users]
        for user in users:
            user.quota_used = 0
            user.last_reset = now
            session.add(user)
        await session.commit()
    for user_id in ids:
        await create_notification(user_id, "Monthly quota has been reset.", "system")


async def weekly_trending_summary() -> None:
    trends = await fetch_trends()
    if not trends:
        return
    summary = ", ".join(item["term"] for item in trends[:3])
    async with get_session() as session:
        result = await session.exec(select(User.id))
        user_ids = result.all()
    message = f"Weekly trending keywords: {summary}"
    for user_id in user_ids:
        await create_notification(user_id, message, "summary")


async def daily_product_launch_digest() -> None:
    suggestions = get_product_suggestions()
    if not suggestions:
        return
    top = suggestions[:3]
    summary = "; ".join(
        f"{item['category'].title()}: {item['suggestion']}" for item in top
    )
    async with get_session() as session:
        result = await session.exec(select(User.id))
        user_ids = result.all()
    if not user_ids:
        return
    message = f"Upcoming launch ideas: {summary}"
    for user_id in user_ids:
        await create_notification(user_id, message, "launch")


async def _run_safely(coro) -> None:
    try:
        await coro
    except Exception:
        pass


async def _reset_wrapper() -> None:
    await _run_safely(reset_monthly_quotas())


async def _weekly_wrapper() -> None:
    await _run_safely(weekly_trending_summary())


async def _launch_wrapper() -> None:
    await _run_safely(daily_product_launch_digest())


async def _dispatch_wrapper() -> None:
    await _run_safely(dispatch_due_notifications())


scheduler = AsyncIOScheduler()

scheduler.add_job(
    lambda: asyncio.create_task(_reset_wrapper()),
    trigger="cron",
    day=1,
    hour=0,
    id="notify_monthly_quota_reset",
)

scheduler.add_job(
    lambda: asyncio.create_task(_weekly_wrapper()),
    trigger="cron",
    day_of_week="mon",
    hour=0,
    id="notify_weekly_trends",
)

scheduler.add_job(
    lambda: asyncio.create_task(_launch_wrapper()),
    trigger="cron",
    hour=LAUNCH_DIGEST_HOUR,
    id="notify_launch_digest",
)

scheduler.add_job(
    lambda: asyncio.create_task(_dispatch_wrapper()),
    trigger="interval",
    minutes=DISPATCH_INTERVAL_MINUTES,
    id="notify_dispatch_due",
)


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()
