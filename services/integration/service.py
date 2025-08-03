"""Integration service delegating to API clients."""

from __future__ import annotations

from typing import List

from packages.integrations.printify import get_client as get_printify_client
from packages.integrations.etsy import get_client as get_etsy_client

printify_client = get_printify_client()
etsy_client = get_etsy_client()


async def create_sku(products: List[dict]) -> List[dict]:
    """Attach SKUs to products using Printify."""
    skus = await printify_client.create_skus(products)
    for product, sku in zip(products, skus):
        product["sku"] = sku
    return products


async def publish_listing(product: dict) -> dict:
    """Publish listing to Etsy and attach URLs."""
    url = await etsy_client.publish_listing(product)
    product["etsy_url"] = url
    product["listing_url"] = url
    return product
