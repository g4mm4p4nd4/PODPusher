from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from .service import (
    list_notifications,
    create_notification,
    mark_read,
    start_scheduler,
    schedule_notification,
    list_scheduled_notifications,
    cancel_scheduled_notification,
)
from ..common.observability import register_observability


@asynccontextmanager
async def _notifications_lifespan(_: FastAPI):
    start_scheduler()
    yield


app = FastAPI(lifespan=_notifications_lifespan)
register_observability(app, service_name="notifications")


class NotificationCreate(BaseModel):
    message: str
    type: str = "info"
    user_id: int | None = None


class ScheduledNotificationCreate(BaseModel):
    message: str
    type: str = "info"
    scheduled_for: datetime
    metadata: Dict[str, Any] | None = None
    user_id: Optional[int] = None


class ScheduledNotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    type: str
    scheduled_for: datetime
    status: str
    metadata: Dict[str, Any] | None = None
    created_at: datetime
    dispatched_at: Optional[datetime] = None


def _ensure_user_id(header_value: str | None, fallback: int | None) -> int:
    if fallback is not None:
        return fallback
    if header_value is None:
        raise HTTPException(status_code=400, detail="Missing X-User-Id header")
    return int(header_value)


def _scheduled_response(data: dict) -> ScheduledNotificationResponse:
    payload = {
        **data,
        "scheduled_for": datetime.fromisoformat(data["scheduled_for"]),
        "created_at": datetime.fromisoformat(data["created_at"]),
        "dispatched_at": datetime.fromisoformat(data["dispatched_at"]) if data["dispatched_at"] else None,
    }
    return ScheduledNotificationResponse(**payload)


@app.get("/")
async def get_notifications(x_user_id: str = Header(..., alias="X-User-Id")):
    return await list_notifications(int(x_user_id))


@app.post("/")
async def create_notification_endpoint(
    payload: NotificationCreate,
    x_user_id: str = Header(None, alias="X-User-Id"),
):
    user_id = _ensure_user_id(x_user_id, payload.user_id)
    return await create_notification(user_id, payload.message, payload.type)


@app.put("/{notification_id}/read")
async def mark_read_endpoint(notification_id: int):
    notif = await mark_read(notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif


@app.get("/scheduled", response_model=list[ScheduledNotificationResponse])
async def list_scheduled_endpoint(x_user_id: str = Header(..., alias="X-User-Id")):
    items = await list_scheduled_notifications(int(x_user_id))
    return [_scheduled_response(item) for item in items]


@app.post("/scheduled", response_model=ScheduledNotificationResponse)
async def create_scheduled_endpoint(
    payload: ScheduledNotificationCreate,
    x_user_id: str = Header(None, alias="X-User-Id"),
):
    user_id = _ensure_user_id(x_user_id, payload.user_id)
    record = await schedule_notification(
        user_id,
        payload.message,
        payload.type,
        scheduled_for=payload.scheduled_for,
        metadata=payload.metadata,
    )
    return _scheduled_response(record)


@app.delete("/scheduled/{job_id}", response_model=ScheduledNotificationResponse)
async def cancel_scheduled_endpoint(
    job_id: int,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    record = await cancel_scheduled_notification(job_id)
    if not record or record["user_id"] != int(x_user_id):
        raise HTTPException(status_code=404, detail="Scheduled notification not found")
    return _scheduled_response(record)
