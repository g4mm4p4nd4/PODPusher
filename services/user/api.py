import re
from datetime import datetime

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from pydantic import BaseModel, field_validator

from ..common.auth import ensure_user_record, require_user_id
from ..common.database import get_session
from ..common.observability import register_observability
from ..common.quotas import ensure_quota_state
from ..models import User

router = APIRouter(prefix="/api/user")


@router.get("/me")
async def user_me(user_id: int = Depends(require_user_id)):
    user = await ensure_user_record(user_id)
    return {
        "plan": user.plan,
        "quota_used": user.quota_used,
        "quota_limit": user.quota_limit,
    }


class QuotaUpdate(BaseModel):
    count: int


@router.post("/me")
async def increment_quota(
    data: QuotaUpdate,
    user_id: int = Depends(require_user_id),
):
    async with get_session() as session:
        user = await session.get(User, user_id)
        now = datetime.utcnow()
        if not user:
            user = User(id=user_id, last_reset=now)
        if ensure_quota_state(user, now):
            session.add(user)
        limit = user.quota_limit
        if limit is not None and user.quota_used + data.count > limit:
            raise HTTPException(status_code=403, detail="Quota exceeded")
        user.quota_used += data.count
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return {
            "plan": user.plan,
            "quota_used": user.quota_used,
            "quota_limit": user.quota_limit,
        }


HANDLE_PATTERN = re.compile(r"^@?[a-zA-Z0-9_.]{1,30}$")


class Preferences(BaseModel):
    auto_social: bool = True
    social_handles: dict[str, str] = {}
    email_notifications: bool = True
    push_notifications: bool = False
    preferred_language: str = "en"
    preferred_currency: str = "USD"
    timezone: str = "UTC"

    @field_validator("social_handles")
    @classmethod
    def validate_handles(cls, value: dict[str, str]) -> dict[str, str]:
        for network, handle in value.items():
            if handle and not HANDLE_PATTERN.match(handle):
                raise ValueError(
                    f"Invalid handle for {network}: must be 1-30 alphanumeric/underscore/dot chars, optional leading @"
                )
        return value


@router.get("/preferences")
async def get_preferences(user_id: int = Depends(require_user_id)):
    async with get_session() as session:
        user = await session.get(User, user_id)
        if not user:
            user = User(id=user_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return {
            "auto_social": user.auto_social,
            "social_handles": user.social_handles,
            "email_notifications": user.email_notifications,
            "push_notifications": user.push_notifications,
            "preferred_language": user.preferred_language,
            "preferred_currency": user.preferred_currency,
            "timezone": user.timezone,
        }


@router.post("/preferences")
async def set_preferences(
    data: Preferences,
    user_id: int = Depends(require_user_id),
):
    async with get_session() as session:
        user = await session.get(User, user_id)
        if not user:
            user = User(id=user_id)
        user.auto_social = data.auto_social
        user.social_handles = data.social_handles
        user.email_notifications = data.email_notifications
        user.push_notifications = data.push_notifications
        user.preferred_language = data.preferred_language
        user.preferred_currency = data.preferred_currency
        user.timezone = data.timezone
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return {
            "auto_social": user.auto_social,
            "social_handles": user.social_handles,
            "email_notifications": user.email_notifications,
            "push_notifications": user.push_notifications,
            "preferred_language": user.preferred_language,
            "preferred_currency": user.preferred_currency,
            "timezone": user.timezone,
        }


app = FastAPI()
register_observability(app, service_name="user")
app.include_router(router)
