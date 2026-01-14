from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Request, status

from ..auth import service as auth_service
from ..models import User
from .database import get_session
from .quotas import ensure_quota_state


async def require_user_id(request: Request) -> int:
    auth_header = request.headers.get("Authorization")
    if auth_header:
        prefix, _, token = auth_header.partition(" ")
        if prefix.lower() == "bearer" and token:
            user_id = await auth_service.resolve_session_token(token)
            if user_id is not None:
                return user_id
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
    auth_header = request.headers.get("Authorization")
    if auth_header:
        prefix, _, token = auth_header.partition(" ")
        if prefix.lower() == "bearer" and token:
            user_id = await auth_service.resolve_session_token(token)
            if user_id is not None:
                return user_id
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
