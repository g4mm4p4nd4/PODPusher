from __future__ import annotations

import logging
import os
from typing import List, Dict, Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)
API_BASE = "https://api.printify.com/v1"


class ProductBlueprint(BaseModel):
    """Simple blueprint descriptor for product variants."""

    blueprint_id: str
    colors: List[str]
    sizes: List[str]


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


def _create_product_real(
    api_key: str,
    idea_id: str,
    image_ids: List[str],
    blueprint_id: str,
    variants: List[str],
    mockups: Optional[List[str]] = None,
) -> Dict:
    """Call Printify to create a product with the given variants."""

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "title": f"Idea {idea_id}",
        "blueprint_id": blueprint_id,
        "print_provider_id": 1,
        "variants": [{"id": v} for v in variants],
        "images": [{"src": img} for img in (mockups or image_ids)],
    }
    try:
        resp = httpx.post(
            f"{API_BASE}/products.json", json=payload, headers=headers, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        variant_ids = [str(v.get("id", "")) for v in data.get("variants", [])]
        return {"product_id": str(data.get("id", "")), "variant_ids": variant_ids}
    except httpx.HTTPError as exc:
        logger.error("Printify API error: %s", exc)
        raise


def _create_product_stub(
    idea_id: str,
    image_ids: List[str],
    blueprint_id: str,
    variants: List[str],
    mockups: Optional[List[str]] = None,
) -> Dict:
    logger.info("PRINTIFY_API_KEY missing; returning stub product")
    variant_ids = [f"stub-var-{i}" for i, _ in enumerate(variants, start=1)]
    return {"product_id": "stub-product", "variant_ids": variant_ids}


def create_product(
    idea_id: str,
    image_ids: List[str],
    blueprint_id: str,
    variants: List[str],
    mockups: Optional[List[str]] = None,
) -> Dict:
    api_key = os.getenv("PRINTIFY_API_KEY")
    if not api_key:
        return _create_product_stub(idea_id, image_ids, blueprint_id, variants, mockups)
    return _create_product_real(api_key, idea_id, image_ids, blueprint_id, variants, mockups)
