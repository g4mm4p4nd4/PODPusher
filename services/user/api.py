from datetime import datetime
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ..common.database import get_session
from ..models import User
from ..common.quotas import PLAN_LIMITS

app = FastAPI()


class UsageUpdate(BaseModel):
    increment: int


@app.get("/plan")
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


@app.post("/plan")
async def update_quota(
    data: UsageUpdate, x_user_id: str = Header(..., alias="X-User-Id")
):
    async with get_session() as session:
        user = await session.get(User, int(x_user_id))
        if not user:
            user = User(id=int(x_user_id))
        limit = PLAN_LIMITS.get(user.plan, PLAN_LIMITS["free"])
        if user.quota_used + data.increment > limit:
            return JSONResponse({"detail": "Quota exceeded"}, status_code=403)
        user.quota_used += data.increment
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return {"plan": user.plan, "quota_used": user.quota_used, "limit": limit}
