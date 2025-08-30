from datetime import datetime
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from ..common.database import get_session
from ..models import User
from ..common.quotas import PLAN_LIMITS

app = FastAPI()


@app.get("/api/user/plan")
async def user_plan(x_user_id: str = Header(..., alias="X-User-Id")):
    async with get_session() as session:
        user = await session.get(User, int(x_user_id))
        now = datetime.utcnow()
        if not user:
            user = User(id=int(x_user_id), last_reset=now)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            if user.last_reset.month != now.month or user.last_reset.year != now.year:
                user.quota_used = 0
                user.last_reset = now
                session.add(user)
                await session.commit()
                await session.refresh(user)
        limit = PLAN_LIMITS.get(user.plan, PLAN_LIMITS["free"])
        return {"plan": user.plan, "quota_used": user.quota_used, "limit": limit}


class QuotaUpdate(BaseModel):
    count: int


@app.post("/api/user/plan")
async def increment_quota(
    data: QuotaUpdate, x_user_id: str = Header(..., alias="X-User-Id")
):  # noqa: E501
    async with get_session() as session:
        user = await session.get(User, int(x_user_id))
        if not user:
            user = User(id=int(x_user_id))
            session.add(user)
            await session.commit()
            await session.refresh(user)
        limit = PLAN_LIMITS.get(user.plan, PLAN_LIMITS["free"])
        if user.quota_used + data.count > limit:
            raise HTTPException(status_code=403, detail="Quota exceeded")
        user.quota_used += data.count
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return {"plan": user.plan, "quota_used": user.quota_used, "limit": limit}
