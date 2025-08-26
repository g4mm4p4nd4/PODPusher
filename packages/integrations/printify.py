from __future__ import annotations

import logging
import os
from typing import List, Dict

import httpx

logger = logging.getLogger(__name__)
API_BASE = "https://api.printify.com/v1"


def _create_sku_real(api_key: str, products: List[Dict]) -> List[Dict]:
    headers = {"Authorization": f"Bearer {api_key}"}
    skus: List[str] = []
    for product in products:
        try:
            resp = httpx.post(
                f"{API_BASE}/products.json", json=product, headers=headers, timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            skus.append(str(data.get("id", "")))
        except httpx.HTTPError as exc:
            logger.error("Printify API error: %s", exc)
            raise
    for product, sku in zip(products, skus):
        product["sku"] = sku
    return products


def _create_sku_stub(products: List[Dict]) -> List[Dict]:
    logger.info("PRINTIFY_API_KEY missing; using stub client")
    for i, product in enumerate(products, start=1):
        product["sku"] = f"stub-sku-{i}"
    return products


def get_printify_client():
    api_key = os.getenv("PRINTIFY_API_KEY")
    if not api_key:
        return _create_sku_stub
    return lambda products: _create_sku_real(api_key, products)
