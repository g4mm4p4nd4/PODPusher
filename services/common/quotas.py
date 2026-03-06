"""Quota management with billing integration."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from .database import get_session
from ..models import User

logger = logging.getLogger(__name__)

# Legacy plan limits (kept for backwards compatibility)
LEGACY_PLAN_LIMITS = {"free": 20, "pro": None}


def plan_limit(plan: str) -> Optional[int]:
    """Return the default quota limit for a legacy plan.

    Deprecated: Use get_user_quota_limits() for billing-aware limits.
    """
    return LEGACY_PLAN_LIMITS.get(plan, LEGACY_PLAN_LIMITS["free"])


async def get_user_plan_tier(user_id: int) -> str:
    """Get the user's plan tier from billing service.

    Returns the plan tier string (free, starter, professional, enterprise).
    """
    try:
        from ..billing.service import get_user_plan_tier as billing_get_tier
        tier = await billing_get_tier(user_id)
        return tier.value
    except Exception as e:
        logger.warning(f"Failed to get plan tier for user {user_id}: {e}")
        return "free"


async def get_user_quota_limits(user_id: int) -> dict:
    """Get quota limits based on user's billing plan.

    Returns a dict with monthly_listings, monthly_images, monthly_ideas.
    """
    try:
        from ..billing.plans import PlanTier, get_plan_limits
        from ..billing.service import get_user_plan_tier as billing_get_tier

        tier = await billing_get_tier(user_id)
        limits = get_plan_limits(tier)

        return {
            "plan_tier": tier.value,
            "monthly_listings": limits.monthly_listings,
            "monthly_images": limits.monthly_images,
            "monthly_ideas": limits.monthly_ideas,
            "team_seats": limits.team_seats,
            "priority_support": limits.priority_support,
        }
    except Exception as e:
        logger.warning(f"Failed to get quota limits for user {user_id}: {e}")
        # Fallback to free tier defaults
        return {
            "plan_tier": "free",
            "monthly_listings": 10,
            "monthly_images": 20,
            "monthly_ideas": 50,
            "team_seats": 1,
            "priority_support": False,
        }


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


async def check_quota(user_id: int, resource_type: str, count: int = 1) -> tuple[bool, dict]:
    """Check if user has quota available for the requested resource.

    Args:
        user_id: The user's ID
        resource_type: One of 'listings', 'images', 'ideas'
        count: Number of resources being used

    Returns:
        Tuple of (allowed: bool, details: dict)
        details includes current usage, limit, and remaining
    """
    limits = await get_user_quota_limits(user_id)

    limit_key = f"monthly_{resource_type}"
    limit = limits.get(limit_key)

    if limit is None:
        # No limit configured for this resource
        return True, {"allowed": True, "limit": None, "used": 0, "remaining": None}

    # Get current usage from database
    async with get_session() as session:
        user = await session.get(User, user_id)
        now = datetime.utcnow()

        if not user:
            user = User(id=user_id, last_reset=now)
            ensure_quota_state(user, now)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            if ensure_quota_state(user, now):
                session.add(user)
                await session.commit()
                await session.refresh(user)

        # For now, use quota_used as a general counter
        # In a full implementation, we'd track per-resource-type usage
        used = user.quota_used
        remaining = max(0, limit - used)
        allowed = used + count <= limit

        return allowed, {
            "allowed": allowed,
            "limit": limit,
            "used": used,
            "remaining": remaining,
            "plan_tier": limits["plan_tier"],
        }


async def increment_quota(user_id: int, resource_type: str, count: int = 1) -> dict:
    """Increment quota usage for a user.

    Returns updated usage info.
    """
    async with get_session() as session:
        user = await session.get(User, user_id)
        now = datetime.utcnow()

        if not user:
            user = User(id=user_id, last_reset=now)
            ensure_quota_state(user, now)
            session.add(user)

        user.quota_used += count
        session.add(user)
        await session.commit()
        await session.refresh(user)

        return {
            "used": user.quota_used,
            "limit": user.quota_limit,
        }


async def quota_middleware(request: Request, call_next):
    """Middleware to enforce quotas on image generation endpoint."""
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

    # Check quota using billing-aware limits
    allowed, details = await check_quota(int(user_id), "images", count)

    if not allowed:
        return JSONResponse(
            {
                "detail": "Quota exceeded",
                "code": "QUOTA_EXCEEDED",
                "limit": details["limit"],
                "used": details["used"],
                "plan_tier": details["plan_tier"],
                "upgrade_url": "/api/billing/portal",
            },
            status_code=402,  # Payment Required - per AU-05
        )

    response = await call_next(request)

    # Increment usage on success
    if response.status_code < 400:
        await increment_quota(int(user_id), "images", count)

    return response
