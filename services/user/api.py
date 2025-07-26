from fastapi import FastAPI, Header, HTTPException
from datetime import datetime
from ..common.database import get_session
from ..models import User
from sqlmodel import select
from ..common.quotas import PLAN_LIMITS

app = FastAPI()


@app.get("/user/plan")
async def user_plan(x_user_id: int | None = Header(None)):
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="User ID required")
    async with get_session() as session:
        result = await session.exec(select(User).where(User.id == x_user_id))
        user = result.first()
        if not user:
            user = User(id=x_user_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        now = datetime.utcnow()
        if user.last_reset.month != now.month or user.last_reset.year != now.year:
            user.images_used = 0
            user.last_reset = now
            await session.commit()
        limit = PLAN_LIMITS.get(user.plan, PLAN_LIMITS["free"])
        return {"plan": user.plan, "images_used": user.images_used, "limit": limit}
