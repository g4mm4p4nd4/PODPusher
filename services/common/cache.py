"""In-memory response cache with TTL support.

Provides a lightweight caching layer for read-heavy endpoints.
Uses Redis when available, falls back to an in-memory LRU cache.

Owner: Backend-Coder (per DEVELOPMENT_PLAN.md Task 2.3.1)
Reference: BC-08 (Performance & Scalability)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)

# Try to import Redis; fall back to in-memory cache
_redis_client = None

try:
    import redis

    REDIS_URL = os.getenv("REDIS_URL")
    if REDIS_URL:
        _redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        _redis_client.ping()
        logger.info("Redis cache connected: %s", REDIS_URL)
except Exception:
    _redis_client = None
    logger.info("Redis not available; using in-memory cache")


class InMemoryCache:
    """Thread-safe in-memory LRU cache with TTL support."""

    def __init__(self, max_size: int = 1024):
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._max_size = max_size

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        # Move to end (most recently used)
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        expires_at = time.time() + ttl
        self._store[key] = (expires_at, value)
        self._store.move_to_end(key)
        # Evict oldest entries if over capacity
        while len(self._store) > self._max_size:
            self._store.popitem(last=False)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


# Singleton in-memory cache
_mem_cache = InMemoryCache()


def cache_key(*parts: str) -> str:
    """Build a cache key from parts."""
    raw = ":".join(str(p) for p in parts)
    return f"pod:{hashlib.md5(raw.encode()).hexdigest()}"


def cache_get(key: str) -> Any | None:
    """Get a value from cache."""
    if _redis_client:
        try:
            raw = _redis_client.get(key)
            if raw is not None:
                return json.loads(raw)
        except Exception:
            pass
    return _mem_cache.get(key)


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Set a value in cache with TTL (seconds)."""
    if _redis_client:
        try:
            _redis_client.setex(key, ttl, json.dumps(value, default=str))
            return
        except Exception:
            pass
    _mem_cache.set(key, value, ttl)


def cache_delete(key: str) -> None:
    """Delete a value from cache."""
    if _redis_client:
        try:
            _redis_client.delete(key)
        except Exception:
            pass
    _mem_cache.delete(key)


def cache_clear() -> None:
    """Clear all cached values."""
    if _redis_client:
        try:
            # Only clear keys with our prefix
            for k in _redis_client.scan_iter("pod:*"):
                _redis_client.delete(k)
        except Exception:
            pass
    _mem_cache.clear()


# Default TTLs for different data types
CACHE_TTL_TRENDS = int(os.getenv("CACHE_TTL_TRENDS", "300"))        # 5 min
CACHE_TTL_IDEAS = int(os.getenv("CACHE_TTL_IDEAS", "600"))          # 10 min
CACHE_TTL_USER_QUOTA = int(os.getenv("CACHE_TTL_USER_QUOTA", "60")) # 1 min
