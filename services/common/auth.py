from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Request, status

from ..auth import service as auth_service
from ..models import User
from .database import get_session
from .quotas import ensure_quota_state


async def _resolve_bearer_user_id(request: Request) -> tuple[bool, Optional[int]]:
    """Resolve a bearer token user id.

    Returns a tuple of (authorization_header_present, resolved_user_id).
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return False, None

    prefix, _, token = auth_header.partition(" ")
    if prefix.lower() != "bearer" or not token:
        return True, None

    user_id = await auth_service.resolve_session_token(token)
    return True, user_id


async def require_user_id(request: Request) -> int:
    auth_present, bearer_user_id = await _resolve_bearer_user_id(request)
    if auth_present:
        if bearer_user_id is not None:
            return bearer_user_id
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    user_header = request.headers.get("X-User-Id")
    if user_header:
        try:
            return int(user_header)
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-User-Id header",
            ) from exc
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


async def optional_user_id(request: Request) -> Optional[int]:
    auth_present, bearer_user_id = await _resolve_bearer_user_id(request)
    if auth_present:
        return bearer_user_id

    user_header = request.headers.get("X-User-Id")
    if user_header:
        try:
            return int(user_header)
        except ValueError:
            return None
    return None


async def ensure_user_record(user_id: int) -> User:
    async with get_session() as session:
        now = datetime.utcnow()
        user = await session.get(User, user_id)
        if not user:
            user = User(id=user_id, last_reset=now)
            ensure_quota_state(user, now)
            session.add(user)
        else:
            if ensure_quota_state(user, now):
                session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
