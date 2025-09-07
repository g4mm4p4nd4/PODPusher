from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel

from .service import (
    DeliveryMethod,
    NotificationService,
    NotificationStatus,
    NotificationType,
    get_service,
)

app = FastAPI()


@app.on_event("startup")
async def start(service: NotificationService = Depends(get_service)) -> None:
    service.start()


class SchedulePayload(BaseModel):
    type: NotificationType
    message: str
    delivery_method: DeliveryMethod = DeliveryMethod.in_app
    scheduled_at: Optional[datetime] = None


@app.post("/api/notifications/schedule")
async def schedule_notification(
    payload: SchedulePayload,
    x_user_id: str = Header(..., alias="X-User-Id"),
    service: NotificationService = Depends(get_service),
):
    notif = await service.schedule_notification(
        int(x_user_id),
        payload.type,
        payload.message,
        payload.delivery_method,
        payload.scheduled_at,
    )
    return service.to_dict(notif)


@app.get("/api/notifications")
async def list_notifications_endpoint(
    x_user_id: str = Header(..., alias="X-User-Id"),
    unread: Optional[bool] = Query(None),
    status: Optional[NotificationStatus] = Query(None),
    service: NotificationService = Depends(get_service),
):
    notifs = await service.list_notifications(
        int(x_user_id), unread=unread, status=status
    )
    return [service.to_dict(n) for n in notifs]


class MarkReadPayload(BaseModel):
    id: int


@app.post("/api/notifications/mark_read")
async def mark_read_endpoint(
    payload: MarkReadPayload,
    x_user_id: str = Header(..., alias="X-User-Id"),
    service: NotificationService = Depends(get_service),
):
    notif = await service.mark_read(payload.id, int(x_user_id))
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return service.to_dict(notif)


class PreferencePayload(BaseModel):
    type: NotificationType
    delivery_method: DeliveryMethod


@app.post("/api/notifications/preferences")
async def set_preferences(
    payload: PreferencePayload,
    x_user_id: str = Header(..., alias="X-User-Id"),
    service: NotificationService = Depends(get_service),
):
    pref = await service.set_preference(
        int(x_user_id), payload.type, payload.delivery_method
    )
    return {
        "id": pref.id,
        "user_id": pref.user_id,
        "type": pref.type,
        "delivery_method": pref.delivery_method,
    }
