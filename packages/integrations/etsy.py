"""Etsy API client with stub fallback.

Handles authentication, simple rate limiting and retries.
Falls back to a deterministic stub when the ``ETSY_API_KEY``
environment variable is missing or ``ETSY_USE_STUB`` is truthy.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

BASE_URL = "https://openapi.etsy.com/v3/application"
API_KEY = os.getenv("ETSY_API_KEY")
USE_STUB = os.getenv("ETSY_USE_STUB", "0").lower() in {"1", "true", "yes"}

RATE_LIMIT = 10  # requests per second


class EtsyClient:
    def __init__(self, api_key: str):
        self.headers = {"x-api-key": api_key}
        self._lock = asyncio.Lock()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        async with self._lock:
            await asyncio.sleep(1 / RATE_LIMIT)
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:
            for attempt in range(3):
                resp = await client.request(
                    method, path, headers=self.headers, **kwargs
                )
                if resp.status_code in {429} or resp.status_code >= 500:
                    await asyncio.sleep(2**attempt)
                    continue
                resp.raise_for_status()
                return resp.json()
        raise RuntimeError("Etsy request failed after retries")

    async def publish_listing(self, product: dict) -> str:
        data = await self._request("post", "/listings", json=product)
        return data.get("url", "")


class EtsyStubClient:
    async def publish_listing(self, product: dict) -> str:
        return "http://etsy.example/listing"


def get_client() -> EtsyClient | EtsyStubClient:
    if USE_STUB or not API_KEY:
        return EtsyStubClient()
    return EtsyClient(API_KEY)
