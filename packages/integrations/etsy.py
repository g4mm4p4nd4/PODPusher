from __future__ import annotations

import logging
import os
from typing import Dict

import httpx

logger = logging.getLogger(__name__)
API_BASE = "https://openapi.etsy.com/v3/application"


def _publish_listing_real(api_key: str, product: Dict) -> Dict:
    headers = {"x-api-key": api_key}
    try:
        resp = httpx.post(
            f"{API_BASE}/listings", json=product, headers=headers, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        url = data.get("url", "")
    except httpx.HTTPError as exc:
        logger.error("Etsy API error: %s", exc)
        raise
    product["etsy_url"] = url
    product["listing_url"] = url
    return product


def _publish_listing_stub(product: Dict) -> Dict:
    logger.info("ETSY_API_KEY missing; using stub client")
    url = "http://etsy.example/listing"
    product["etsy_url"] = url
    product["listing_url"] = url
    return product


def get_etsy_client():
    api_key = os.getenv("ETSY_API_KEY")
    if not api_key:
        return _publish_listing_stub
    return lambda product: _publish_listing_real(api_key, product)
