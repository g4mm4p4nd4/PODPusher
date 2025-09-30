from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from ..common.database import get_session
from ..models import User
from ..common.quotas import ensure_quota_state
from ..common.auth import ensure_user_record, require_user_id

app = FastAPI()


@app.get("/api/user/me")
async def user_me(user_id: int = Depends(require_user_id)):
    user = await ensure_user_record(user_id)
    return {
        "plan": user.plan,
        "quota_used": user.quota_used,
        "quota_limit": user.quota_limit,
    }


class QuotaUpdate(BaseModel):
    count: int


@app.post("/api/user/me")
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


class Preferences(BaseModel):
    auto_social: bool = True
    social_handles: dict[str, str] = {}


@app.get("/api/user/preferences")
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
        }


@app.post("/api/user/preferences")
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
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return {
            "auto_social": user.auto_social,
            "social_handles": user.social_handles,
        }
