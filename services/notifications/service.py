from datetime import datetime
import asyncio
from typing import List
from sqlmodel import select

from ..models import Notification, User
from ..common.database import get_session
from ..trend_scraper.service import get_trending_categories


async def create_notification(user_id: int, message: str) -> Notification:
    async with get_session() as session:
        notif = Notification(user_id=user_id, message=message)
        session.add(notif)
        await session.commit()
        await session.refresh(notif)
        return notif


async def list_notifications(user_id: int) -> List[Notification]:
    async with get_session() as session:
        result = await session.exec(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        return result.all()


async def mark_read(notification_id: int) -> None:
    async with get_session() as session:
        notif = await session.get(Notification, notification_id)
        if notif:
            notif.read = True
            session.add(notif)
            await session.commit()


async def send_monthly_quota_reset() -> None:
    async with get_session() as session:
        users = await session.exec(select(User))
        for user in users.all():
            uid = user.id
            user.images_used = 0
            user.last_reset = datetime.utcnow()
            session.add(user)
            await session.commit()
            await create_notification(uid, "Your monthly image quota has been reset.")


async def send_weekly_trends() -> None:
    categories = get_trending_categories(None)
    summary = ", ".join(categories.keys())
    async with get_session() as session:
        users = await session.exec(select(User))
        for user in users.all():
            await create_notification(user.id, f"Trending categories: {summary}")


async def start_scheduler() -> None:
    async def monthly_loop() -> None:
        while True:
            now = datetime.utcnow()
            next_month = datetime(now.year + (now.month == 12), (now.month % 12) + 1, 1)
            await asyncio.sleep((next_month - now).total_seconds())
            await send_monthly_quota_reset()

    async def weekly_loop() -> None:
        while True:
            await asyncio.sleep(7 * 24 * 3600)
            await send_weekly_trends()

    asyncio.create_task(monthly_loop())
    asyncio.create_task(weekly_loop())
