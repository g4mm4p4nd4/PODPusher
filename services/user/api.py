from datetime import datetime
from fastapi import FastAPI, Header
from ..common.database import get_session
from ..models import User
from ..common.quotas import PLAN_LIMITS

app = FastAPI()


@app.get("/user/plan")
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
                user.images_used = 0
                user.last_reset = now
                session.add(user)
                await session.commit()
                await session.refresh(user)
        limit = PLAN_LIMITS.get(user.plan, PLAN_LIMITS["free"])
        return {"plan": user.plan, "images_used": user.images_used, "limit": limit}
