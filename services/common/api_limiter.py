"""External API rate limiting using async token buckets.

Enforces per-provider rate limits to avoid exceeding third-party API quotas.

Owner: Backend-Coder (per DEVELOPMENT_PLAN.md Task 2.2.2)
Reference: BC-08 §7 "Rate-limit external API calls"
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AsyncTokenBucket:
    """Async-compatible token bucket rate limiter."""

    rate: float  # tokens per second
    capacity: float
    tokens: float = 0.0
    last_refill: float = field(default_factory=time.monotonic)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def __post_init__(self):
        self.tokens = self.capacity

    async def acquire(self) -> None:
        """Wait until a token is available, then consume it."""
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.last_refill = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return

                # Calculate wait time for next token
                wait_time = (1 - self.tokens) / self.rate
                # Release lock during wait
                self._lock.release()
                try:
                    await asyncio.sleep(wait_time)
                finally:
                    await self._lock.acquire()


# Provider rate limit configuration (requests per second)
PROVIDER_LIMITS: dict[str, tuple[float, float]] = {
    # (rate tokens/sec, burst capacity)
    "printify": (5.0, 10.0),   # 5 req/s per BC §7
    "etsy": (10.0, 20.0),      # 10 req/s per BC §7
    "openai": (3.0, 5.0),      # Conservative limit for OpenAI
    "stripe": (25.0, 50.0),    # Stripe is generous
}

# Singleton rate limiters per provider
_provider_limiters: dict[str, AsyncTokenBucket] = {}


def get_provider_limiter(provider: str) -> AsyncTokenBucket:
    """Get or create a rate limiter for a provider."""
    if provider not in _provider_limiters:
        rate, capacity = PROVIDER_LIMITS.get(provider, (10.0, 20.0))
        _provider_limiters[provider] = AsyncTokenBucket(rate=rate, capacity=capacity)
    return _provider_limiters[provider]


async def rate_limited_call(provider: str, func, *args, **kwargs):
    """Execute a function with rate limiting for the given provider.

    Waits for a token before executing the call.
    """
    limiter = get_provider_limiter(provider)
    await limiter.acquire()
    logger.debug("Rate limiter acquired for %s", provider)
    return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
