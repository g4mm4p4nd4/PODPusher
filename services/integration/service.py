from __future__ import annotations

from typing import List

from packages.integrations.printify import get_printify_client
from packages.integrations.etsy import get_etsy_client


def create_sku(products: List[dict]) -> List[dict]:
    client = get_printify_client()
    return client(products)


def publish_listing(product: dict) -> dict:
    client = get_etsy_client()
    return client(product)
