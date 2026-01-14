from __future__ import annotations

import logging
import os
from copy import deepcopy
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)
API_BASE = "https://api.printify.com/v1"

CATEGORY_DEFAULTS: Dict[str, str] = {
    "apparel": "bella_canvas_3001",
    "home_decor": "mug_11oz",
    "drinkware": "mug_11oz",
    "accessories": "gildan_18500",
}

PRODUCT_TEMPLATES: Dict[str, Dict] = {
    "bella_canvas_3001": {
        "title": "Bella+Canvas 3001 Unisex Tee",
        "description": "Soft cotton tee with a modern retail fit.",
        "blueprint_id": 6,
        "print_provider_id": 1,
        "default_price": 2199,
        "variants": [
            {"id": 4011, "name": "S"},
            {"id": 4012, "name": "M"},
            {"id": 4013, "name": "L"},
        ],
        "options": [{"name": "color", "values": ["white"]}],
        "placement": "front",
    },
    "gildan_18500": {
        "title": "Gildan 18500 Hoodie",
        "description": "Classic hoodie with soft interior and generous fit.",
        "blueprint_id": 18,
        "print_provider_id": 1,
        "default_price": 3599,
        "variants": [
            {"id": 5032, "name": "M"},
            {"id": 5033, "name": "L"},
        ],
        "options": [{"name": "color", "values": ["black"]}],
        "placement": "front",
    },
    "mug_11oz": {
        "title": "11oz Ceramic Mug",
        "description": "Glossy ceramic mug ready for your design.",
        "blueprint_id": 13,
        "print_provider_id": 1,
        "default_price": 1499,
        "variants": [{"id": 6015, "name": "11oz"}],
        "options": [{"name": "color", "values": ["white"]}],
        "placement": "front",
    },
}


def _resolve_template(product: Dict) -> Dict:
    template_key = product.get("template") or CATEGORY_DEFAULTS.get(
        (product.get("category") or "apparel").lower(),
        "bella_canvas_3001",
    )
    template = PRODUCT_TEMPLATES.get(template_key)
    if not template:
        raise ValueError(f"Unknown Printify template '{template_key}'")
    return template


def _price_cents(product: Dict, template: Dict) -> int:
    price = product.get("price")
    if price is None:
        return template.get("default_price", 1999)
    if isinstance(price, str):
        try:
            price = float(price)
        except ValueError:
            return template.get("default_price", 1999)
    if isinstance(price, (int, float)):
        return int(round(float(price) * 100)) if float(price) <= 999 else int(price)
    return template.get("default_price", 1999)


def build_printify_payload(product: Dict) -> Dict:
    if {"blueprint_id", "print_provider_id"}.issubset(product.keys()):
        return product

    template = _resolve_template(product)
    price_cents = _price_cents(product, template)
    title = product.get("title") or template["title"]
    description = product.get("description") or template["description"]
    image_url = product.get("image_url")
    if not image_url:
        images = product.get("image_urls") or product.get("images")
        if isinstance(images, list) and images:
            candidate = images[0]
            if isinstance(candidate, dict):
                image_url = candidate.get("url")
            elif isinstance(candidate, str):
                image_url = candidate
    if not image_url:
        raise ValueError("Product payload requires 'image_url'")

    payload = {
        "title": title,
        "description": description,
        "blueprint_id": template["blueprint_id"],
        "print_provider_id": template["print_provider_id"],
        "variants": [
            {
                "id": variant["id"],
                "price": price_cents,
                "is_enabled": True,
            }
            for variant in template["variants"]
        ],
        "print_areas": [
            {
                "variant_ids": [v["id"] for v in template["variants"]],
                "placeholders": [
                    {
                        "position": template.get("placement", "front"),
                        "images": [
                            {
                                "id": 0,
                                "type": "image/png",
                                "name": product.get("image_name", "Front"),
                                "url": image_url,
                            }
                        ],
                    }
                ],
            }
        ],
        "tags": product.get("tags", []),
        "options": deepcopy(template.get("options", [])),
    }
    return payload


def _create_sku_stub(products: List[Dict]) -> List[Dict]:
    logger.info("Printify credentials missing; using stub client")
    enriched: List[Dict] = []
    for index, product in enumerate(products, start=1):
        replica = dict(product)
        replica.setdefault("sku", f"stub-sku-{index}")
        replica.setdefault("printify_response", {"id": replica["sku"], "status": "stub"})
        enriched.append(replica)
    return enriched


def _create_sku_real(
    token: str,
    shop_id: str,
    products: List[Dict],
) -> List[Dict]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    created: List[Dict] = []
    with httpx.Client(timeout=20) as client:
        for product in products:
            payload = build_printify_payload(product)
            try:
                response = client.post(
                    f"{API_BASE}/shops/{shop_id}/products.json",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                logger.error("Printify API error: %s", exc)
                raise
            data = response.json()
            replica = dict(product)
            replica["sku"] = str(data.get("id") or data.get("product_id") or data.get("slug") or "")
            replica["printify_response"] = data
            created.append(replica)
    return created


def get_printify_client(credential: Optional[Dict] = None):
    token = None
    shop_id = None
    if credential:
        token = credential.get("access_token")
        shop_id = credential.get("account_id")
    token = token or os.getenv("PRINTIFY_API_KEY")
    shop_id = shop_id or os.getenv("PRINTIFY_SHOP_ID")
    if not token or not shop_id:
        return _create_sku_stub
    return lambda products: _create_sku_real(token, shop_id, products)
