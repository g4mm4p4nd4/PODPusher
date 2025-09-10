from __future__ import annotations

from typing import List

from packages.integrations.printify import (
    get_printify_client,
    create_product as printify_create_product,
)
from packages.integrations.etsy import get_etsy_client
from packages.integrations import gemini


def create_sku(products: List[dict]) -> List[dict]:
    client = get_printify_client()
    return client(products)


def publish_listing(product: dict) -> dict:
    client = get_etsy_client()
    return client(product)


def create_printify_product(
    idea_id: str,
    image_ids: List[str],
    blueprint_id: str,
    variants: List[str],
) -> dict:
    """Create a Printify product and upload mock-up images."""

    mockups = [
        gemini.generate_mockup(f"{blueprint_id} variant {v}") for v in variants
    ]
    return printify_create_product(idea_id, image_ids, blueprint_id, variants, mockups)
