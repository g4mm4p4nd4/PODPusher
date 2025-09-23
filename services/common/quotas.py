import json
from datetime import datetime
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from .database import get_session
from ..models import User

PLAN_LIMITS = {"free": 20, "pro": None}


def plan_limit(plan: str) -> Optional[int]:
    """Return the default quota limit for a plan."""

    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


def ensure_quota_state(user: User, now: datetime) -> bool:
    """Ensure the user's quota window and limits are up to date.

    Returns True when any field was modified.
    """

    changed = False
    if user.last_reset.month != now.month or user.last_reset.year != now.year:
        user.quota_used = 0
        user.last_reset = now
        changed = True

    expected_limit = plan_limit(user.plan)
    if user.quota_limit != expected_limit:
        user.quota_limit = expected_limit
        changed = True

    return changed


async def quota_middleware(request: Request, call_next):
    if request.url.path != "/images" or request.method.upper() != "POST":
        return await call_next(request)

    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return JSONResponse({"detail": "Missing X-User-Id"}, status_code=400)

    body_bytes = await request.body()
    try:
        payload = json.loads(body_bytes)
        count = len(payload.get("ideas", []))
    except Exception:
        count = 1
    request._body = body_bytes  # allow downstream handlers to read body again

    async with get_session() as session:
        user = await session.get(User, int(user_id))
        now = datetime.utcnow()
        if not user:
            user = User(id=int(user_id), last_reset=now)
            ensure_quota_state(user, now)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            if ensure_quota_state(user, now):
                session.add(user)
                await session.commit()
                await session.refresh(user)

        limit = user.quota_limit
        if limit is not None and user.quota_used + count > limit:
            return JSONResponse({"detail": "Quota exceeded"}, status_code=403)

        response = await call_next(request)
        user.quota_used += count
        session.add(user)
        await session.commit()
        return response
