"""Printify API client with stub fallback.

The client handles basic authentication, naive rate limiting
and retry logic. When the ``PRINTIFY_API_KEY`` environment variable
is missing or ``PRINTIFY_USE_STUB`` is truthy, a stub client is
returned instead.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, List

import httpx

BASE_URL = "https://api.printify.com/v1"
API_KEY = os.getenv("PRINTIFY_API_KEY")
SHOP_ID = os.getenv("PRINTIFY_SHOP_ID", "1")
USE_STUB = os.getenv("PRINTIFY_USE_STUB", "0").lower() in {"1", "true", "yes"}

RATE_LIMIT = 5  # requests per second


class PrintifyClient:
    """Minimal Printify client."""

    def __init__(self, api_key: str, shop_id: str = SHOP_ID):
        self.api_key = api_key
        self.shop_id = shop_id
        self.headers = {"Authorization": f"Bearer {api_key}"}
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
        raise RuntimeError("Printify request failed after retries")

    async def create_skus(self, products: List[dict]) -> List[str]:
        """Create products and return their SKUs."""
        skus: List[str] = []
        for product in products:
            data = await self._request(
                "post", f"/shops/{self.shop_id}/products.json", json=product
            )
            skus.append(data.get("sku", ""))
        return skus


class PrintifyStubClient:
    """Deterministic stub for tests and offline mode."""

    async def create_skus(self, products: List[dict]) -> List[str]:
        return [f"stub-sku-{i}" for i, _ in enumerate(products, start=1)]


def get_client() -> PrintifyClient | PrintifyStubClient:
    """Return a real or stub client based on environment."""
    if USE_STUB or not API_KEY:
        return PrintifyStubClient()
    return PrintifyClient(API_KEY, SHOP_ID)
