"""Rate limiting middleware for FastAPI.

Provides per-user and per-IP rate limiting using an in-memory token bucket.
Falls back to a simple in-memory store when Redis is not available.

Owner: Backend-Coder (per DEVELOPMENT_PLAN.md Task 2.2.1)
Reference: BC-08 (Performance & Scalability)
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Plan-tier rate limit configuration (requests per minute)
# ---------------------------------------------------------------------------

PLAN_RATE_LIMITS: dict[str, int] = {
    "free": 30,
    "starter": 60,
    "professional": 120,
    "enterprise": 300,
}

# IP-level rate limit for unauthenticated endpoints (requests per minute)
IP_RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_IP", "60"))


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""

    capacity: int
    tokens: float = 0.0
    last_refill: float = field(default_factory=time.monotonic)

    def __post_init__(self):
        self.tokens = float(self.capacity)

    def allow(self) -> tuple[bool, dict[str, int]]:
        """Check if a request is allowed. Returns (allowed, headers)."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        # Refill at rate of capacity tokens per 60 seconds
        self.tokens = min(self.capacity, self.tokens + elapsed * (self.capacity / 60.0))
        self.last_refill = now

        remaining = max(0, int(self.tokens) - 1)
        reset_seconds = int(60.0 * (1.0 / max(self.capacity / 60.0, 0.001)))

        headers = {
            "X-RateLimit-Limit": str(self.capacity),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(now) + reset_seconds),
        }

        if self.tokens >= 1:
            self.tokens -= 1
            return True, headers

        headers["Retry-After"] = str(reset_seconds)
        return False, headers


class RateLimiter:
    """In-memory rate limiter with per-key token buckets."""

    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}
        self._cleanup_counter = 0

    def check(self, key: str, limit: int) -> tuple[bool, dict[str, int]]:
        """Check rate limit for a key. Creates bucket if needed."""
        bucket = self._buckets.get(key)
        if bucket is None or bucket.capacity != limit:
            bucket = TokenBucket(capacity=limit)
            self._buckets[key] = bucket

        # Periodic cleanup of old buckets
        self._cleanup_counter += 1
        if self._cleanup_counter >= 1000:
            self._cleanup()
            self._cleanup_counter = 0

        return bucket.allow()

    def _cleanup(self):
        """Remove stale buckets older than 5 minutes."""
        now = time.monotonic()
        stale = [k for k, v in self._buckets.items() if now - v.last_refill > 300]
        for k in stale:
            del self._buckets[k]


# Singleton instance
_limiter = RateLimiter()

# Paths excluded from rate limiting
_EXCLUDED_PATHS = {"/healthz", "/metrics", "/docs", "/openapi.json", "/redoc"}


def register_rate_limiting(app: FastAPI) -> None:
    """Attach rate limiting middleware to a FastAPI app."""

    @app.middleware("http")
    async def _rate_limit_middleware(request: Request, call_next: Callable):
        path = request.url.path

        # Skip rate limiting for health/metrics/docs
        if path in _EXCLUDED_PATHS:
            return await call_next(request)

        # Determine rate limit key and limit
        user_id = request.headers.get("X-User-Id")
        if user_id:
            # Per-user rate limiting based on plan tier
            plan = getattr(request.state, "plan", None) or "free"
            limit = PLAN_RATE_LIMITS.get(plan, PLAN_RATE_LIMITS["free"])
            key = f"user:{user_id}"
        else:
            # Per-IP rate limiting for unauthenticated requests
            client_ip = request.client.host if request.client else "unknown"
            limit = IP_RATE_LIMIT
            key = f"ip:{client_ip}"

        allowed, headers = _limiter.check(key, limit)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "code": "RATE_LIMITED",
                    "message": "Too many requests — please slow down",
                    "request_id": getattr(request.state, "request_id", ""),
                },
                headers=headers,
            )

        response = await call_next(request)

        # Add rate limit headers to all responses
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value

        return response
