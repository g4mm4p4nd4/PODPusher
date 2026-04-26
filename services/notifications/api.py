from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from ..common.auth import optional_user_id
from ..control_center.service import (
    create_notification_rule,
    get_notifications_dashboard,
)
from ..auth.service import resolve_session_token
from .service import (
    cancel_scheduled_notification,
    create_automation_job,
    create_notification,
    list_notifications,
    list_scheduled_notifications,
    mark_read_for_user,
    schedule_notification,
    start_scheduler,
    update_notification_preferences,
    update_notification_rule,
)
from ..common.observability import register_observability


@asynccontextmanager
async def _notifications_lifespan(_: FastAPI):
    start_scheduler()
    yield


app = FastAPI(lifespan=_notifications_lifespan)
register_observability(app, service_name="notifications")


class NotificationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str
    type: str = "info"


class ScheduledNotificationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str
    type: str = "info"
    scheduled_for: datetime
    metadata: Dict[str, Any] | None = None


class NotificationRuleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    metric: str = "image_quota_remaining"
    operator: str = "less_than"
    threshold: float = 20
    window: str = "1 day"
    channels: list[str] = Field(default_factory=lambda: ["Email", "In-App"])
    active: bool = True


class NotificationRuleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    metric: str | None = None
    operator: str | None = None
    threshold: float | None = None
    window: str | None = None
    channels: list[str] | None = None
    active: bool | None = None


class AutomationJobCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    frequency: str
    next_run: datetime
    category: str = "digest"
    metadata: Dict[str, Any] | None = None


class NotificationPreferencesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email_enabled: bool | None = None
    in_app_enabled: bool | None = None
    email_critical: bool = True
    email_warnings: bool = True
    email_digest: bool = True
    email_marketing: bool = True
    in_app_critical: bool = True
    in_app_warnings: bool = True
    in_app_info: bool = True


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


def _parse_user_id(
    value: str | None, missing_detail: str = "Missing X-User-Id header"
) -> int:
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
    return _parse_user_id(
        request.headers.get("X-User-Id"), missing_detail=missing_detail
    )


def _scheduled_response(data: dict) -> ScheduledNotificationResponse:
    payload = {
        **data,
        "scheduled_for": datetime.fromisoformat(data["scheduled_for"]),
        "created_at": datetime.fromisoformat(data["created_at"]),
        "dispatched_at": (
            datetime.fromisoformat(data["dispatched_at"])
            if data["dispatched_at"]
            else None
        ),
    }
    return ScheduledNotificationResponse(**payload)


@app.get("/")
async def get_notifications(request: Request):
    return await list_notifications(await _resolve_request_user_id(request))


@app.get("/dashboard")
async def dashboard(user_id: int | None = Depends(optional_user_id)):
    return await get_notifications_dashboard(user_id)


@app.post("/")
async def create_notification_endpoint(
    request: Request,
    payload: NotificationCreate,
):
    user_id = await _resolve_request_user_id(request)
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
    user_id = await _resolve_request_user_id(request)
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


@app.post("/rules")
async def create_rule(
    payload: NotificationRuleCreate,
    user_id: int | None = Depends(optional_user_id),
):
    return await create_notification_rule(user_id, payload.model_dump())


@app.patch("/rules/{rule_id}")
async def update_rule(
    rule_id: int,
    payload: NotificationRuleUpdate,
    user_id: int | None = Depends(optional_user_id),
):
    resolved_user_id = user_id or 1
    record = await update_notification_rule(
        resolved_user_id,
        rule_id,
        payload.model_dump(exclude_unset=True),
    )
    if not record:
        raise HTTPException(status_code=404, detail="Notification rule not found")
    return record


@app.post("/jobs")
async def create_job(
    payload: AutomationJobCreate,
    user_id: int | None = Depends(optional_user_id),
):
    return await create_automation_job(
        user_id or 1,
        payload.name,
        payload.frequency,
        next_run=payload.next_run,
        category=payload.category,
        metadata=payload.metadata,
    )


@app.put("/preferences")
async def update_preferences(
    payload: NotificationPreferencesUpdate,
    user_id: int | None = Depends(optional_user_id),
):
    return await update_notification_preferences(
        user_id or 1,
        payload.model_dump(exclude_unset=True),
    )
