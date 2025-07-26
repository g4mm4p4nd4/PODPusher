from datetime import datetime
import json
from fastapi import Request
from fastapi.responses import JSONResponse

from .database import get_session
from ..models import User
from sqlmodel import select

PLAN_LIMITS = {"free": 20}


async def quota_middleware(request: Request, call_next):
    if request.method == "POST" and request.url.path == "/images":
        body = await request.body()
        try:
            data = json.loads(body.decode())
        except Exception:  # pragma: no cover - invalid JSON handled by FastAPI
            data = {}
        count = len(data.get("ideas", []))

        async def receive() -> dict:  # allows downstream to read body
            return {"type": "http.request", "body": body, "more_body": False}

        request = Request(request.scope, receive)
        user_id = request.headers.get("X-User-Id")
        if user_id:
            async with get_session() as session:
                result = await session.exec(select(User).where(User.id == int(user_id)))
                user = result.first()
                if not user:
                    user = User(id=int(user_id))
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                now = datetime.utcnow()
                if user.last_reset.month != now.month or user.last_reset.year != now.year:
                    user.images_used = 0
                    user.last_reset = now
                limit = PLAN_LIMITS.get(user.plan, PLAN_LIMITS["free"])
                if user.images_used + count > limit:
                    return JSONResponse({"detail": "Image quota exceeded"}, status_code=402)
                response = await call_next(request)
                if response.status_code < 400:
                    user.images_used += count
                    session.add(user)
                    await session.commit()
                return response
        return await call_next(request)
    return await call_next(request)
