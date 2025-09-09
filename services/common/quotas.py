from datetime import datetime
import json
from fastapi import Request
from fastapi.responses import JSONResponse
from .database import get_session
from ..models import User

PLAN_LIMITS = {"free": 20, "pro": 100}


async def quota_middleware(request: Request, call_next):
    if request.url.path not in {"/images", "/generate"} or request.method.upper() != "POST":
        return await call_next(request)

    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return JSONResponse({"detail": "Missing X-User-Id"}, status_code=400)

    body_bytes = await request.body()
    try:
        payload = json.loads(body_bytes)
        if "ideas" in payload:
            count = len(payload.get("ideas", []))
        else:
            count = 1
    except Exception:
        count = 1
    request._body = body_bytes  # allow downstream handlers to read body again

    async with get_session() as session:
        user = await session.get(User, int(user_id))
        now = datetime.utcnow()
        if not user:
            user = User(id=int(user_id), last_reset=now)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            if user.last_reset.month != now.month or user.last_reset.year != now.year:
                user.quota_used = 0
                user.last_reset = now
                session.add(user)
                await session.commit()

        limit = PLAN_LIMITS.get(user.plan, PLAN_LIMITS["free"])
        if user.quota_used + count > limit:
            return JSONResponse({"detail": "Quota exceeded"}, status_code=403)

        response = await call_next(request)
        user.quota_used += count
        session.add(user)
        await session.commit()
        return response
