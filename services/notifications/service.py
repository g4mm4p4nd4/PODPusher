from __future__ import annotations

from datetime import datetime
import asyncio
from typing import List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import select

from ..common.database import get_session
from ..models import (
    DeliveryMethod,
    Notification,
    NotificationPreference,
    NotificationStatus,
    NotificationType,
    User,
)
from ..trend_scraper.service import fetch_trends
from packages.integrations.notifications import send_email, send_push


class NotificationService:
    """Encapsulates notification scheduling and delivery."""

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(
            lambda: asyncio.create_task(self.send_due_notifications()),
            trigger="interval",
            minutes=1,
        )
        self.scheduler.add_job(
            lambda: asyncio.create_task(self.reset_monthly_quotas()),
            trigger="cron",
            day=1,
            hour=0,
        )
        self.scheduler.add_job(
            lambda: asyncio.create_task(self.check_trending_products()),
            trigger="cron",
            minute="*/30",
        )

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    @staticmethod
    def to_dict(notification: Notification) -> dict:
        return {
            "id": notification.id,
            "user_id": notification.user_id,
            "type": notification.type,
            "message": notification.message,
            "delivery_method": notification.delivery_method,
            "status": notification.status,
            "scheduled_at": notification.scheduled_at.isoformat()
            if notification.scheduled_at
            else None,
            "created_at": notification.created_at.isoformat(),
            "read": notification.read,
        }

    async def schedule_notification(
        self,
        user_id: int,
        notif_type: NotificationType,
        message: str,
        delivery_method: DeliveryMethod,
        scheduled_at: Optional[datetime] = None,
    ) -> Notification:
        async with get_session() as session:
            n = Notification(
                user_id=user_id,
                type=notif_type,
                message=message,
                delivery_method=delivery_method,
                scheduled_at=scheduled_at,
            )
            session.add(n)
            await session.commit()
            await session.refresh(n)
            return n

    async def list_notifications(
        self,
        user_id: int,
        *,
        unread: Optional[bool] = None,
        status: Optional[NotificationStatus] = None,
    ) -> List[Notification]:
        async with get_session() as session:
            query = select(Notification).where(Notification.user_id == user_id)
            if unread is not None:
                query = query.where(Notification.read.is_(False if unread else True))
            if status is not None:
                query = query.where(Notification.status == status)
            result = await session.exec(query.order_by(Notification.created_at.desc()))
            return result.all()

    async def mark_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        async with get_session() as session:
            notif = await session.get(Notification, notification_id)
            if not notif or notif.user_id != user_id:
                return None
            notif.read = True
            session.add(notif)
            await session.commit()
            await session.refresh(notif)
            return notif

    async def set_preference(
        self,
        user_id: int,
        notif_type: NotificationType,
        delivery_method: DeliveryMethod,
    ) -> NotificationPreference:
        async with get_session() as session:
            result = await session.exec(
                select(NotificationPreference).where(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.type == notif_type,
                )
            )
            pref = result.first()
            if pref:
                pref.delivery_method = delivery_method
            else:
                pref = NotificationPreference(
                    user_id=user_id,
                    type=notif_type,
                    delivery_method=delivery_method,
                )
            session.add(pref)
            await session.commit()
            await session.refresh(pref)
            return pref

    async def send_due_notifications(self) -> None:
        now = datetime.utcnow()
        async with get_session() as session:
            result = await session.exec(
                select(Notification).where(
                    Notification.status == NotificationStatus.pending,
                    (Notification.scheduled_at.is_(None))
                    | (Notification.scheduled_at <= now),
                )
            )
            notifications = result.all()
            for n in notifications:
                if n.delivery_method == DeliveryMethod.email:
                    send_email(n.user_id, n.message, n.type)
                elif n.delivery_method == DeliveryMethod.push:
                    send_push(n.user_id, n.message, n.type)
                n.status = NotificationStatus.sent
                session.add(n)
            await session.commit()

    async def reset_monthly_quotas(self) -> None:
        now = datetime.utcnow()
        async with get_session() as session:
            result = await session.exec(select(User))
            users = result.all()
            for u in users:
                u.quota_used = 0
                u.last_reset = now
                session.add(u)
            await session.commit()
            ids = [u.id for u in users]
        for uid in ids:
            await self.schedule_notification(
                uid,
                NotificationType.quota_reset,
                "Monthly quota has been reset.",
                DeliveryMethod.in_app,
            )
        await self.send_due_notifications()

    async def check_trending_products(self) -> None:
        trends = await fetch_trends()
        if not trends:
            return
        top = trends[0]["term"]
        async with get_session() as session:
            result = await session.exec(select(User.id))
            user_ids = result.all()
        for uid in user_ids:
            await self.schedule_notification(
                uid,
                NotificationType.trending_product,
                f"Trending product: {top}",
                DeliveryMethod.in_app,
            )
        await self.send_due_notifications()


_service = NotificationService()


def get_service() -> NotificationService:
    return _service
