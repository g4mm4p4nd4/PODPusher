from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from ..auth.service import resolve_session_token
from .service import (
    cancel_scheduled_notification,
    create_notification,
    list_notifications,
    list_scheduled_notifications,
    mark_read_for_user,
    schedule_notification,
    start_scheduler,
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


def _parse_user_id(value: str | None, missing_detail: str = "Missing X-User-Id header") -> int:
    if value is None:
        raise HTTPException(status_code=400, detail=missing_detail)
    try:
        return int(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid X-User-Id header") from exc


async def _resolve_request_user_id(
    request: Request,
    fallback: int | None = None,
    missing_detail: str = "Missing X-User-Id header",
) -> int:
    if fallback is not None:
        return fallback

    auth_header = request.headers.get("Authorization")
    if auth_header:
        prefix, _, token = auth_header.partition(" ")
        if prefix.lower() == "bearer" and token:
            user_id = await resolve_session_token(token)
            if user_id is not None:
                return user_id
            raise HTTPException(status_code=401, detail="Authentication required")
    return _parse_user_id(request.headers.get("X-User-Id"), missing_detail=missing_detail)


def _scheduled_response(data: dict) -> ScheduledNotificationResponse:
    payload = {
        **data,
        "scheduled_for": datetime.fromisoformat(data["scheduled_for"]),
        "created_at": datetime.fromisoformat(data["created_at"]),
        "dispatched_at": datetime.fromisoformat(data["dispatched_at"]) if data["dispatched_at"] else None,
    }
    return ScheduledNotificationResponse(**payload)


@app.get("/")
async def get_notifications(request: Request):
    return await list_notifications(await _resolve_request_user_id(request))


@app.post("/")
async def create_notification_endpoint(
    request: Request,
    payload: NotificationCreate,
):
    user_id = await _resolve_request_user_id(request, fallback=payload.user_id)
    return await create_notification(user_id, payload.message, payload.type)


@app.put("/{notification_id}/read")
async def mark_read_endpoint(
    request: Request,
    notification_id: int,
):
    user_id = await _resolve_request_user_id(request)
    notif = await mark_read_for_user(notification_id, user_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif


@app.get("/scheduled", response_model=list[ScheduledNotificationResponse])
async def list_scheduled_endpoint(request: Request):
    items = await list_scheduled_notifications(await _resolve_request_user_id(request))
    return [_scheduled_response(item) for item in items]


@app.post("/scheduled", response_model=ScheduledNotificationResponse)
async def create_scheduled_endpoint(
    request: Request,
    payload: ScheduledNotificationCreate,
):
    user_id = await _resolve_request_user_id(request, fallback=payload.user_id)
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
    request: Request,
    job_id: int,
):
    user_id = await _resolve_request_user_id(request)
    record = await cancel_scheduled_notification(job_id, user_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scheduled notification not found")
    return _scheduled_response(record)
