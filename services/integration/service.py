from typing import List
import os

PRINTIFY_API_KEY = os.getenv("PRINTIFY_API_KEY")
ETSY_API_KEY = os.getenv("ETSY_API_KEY")


def create_sku(products: List[dict]) -> List[dict]:
    if PRINTIFY_API_KEY:
        # placeholder for real API call
        skus = ["sku123" for _ in products]
    else:
        skus = ["stub-sku" for _ in products]

    for product, sku in zip(products, skus):
        product["sku"] = sku
    return products


def publish_listing(product: dict) -> dict:
    if ETSY_API_KEY:
        # placeholder for real API call
        url = "http://etsy.com/listing"  # stub
    else:
        url = "http://etsy.example/listing"
    product["etsy_url"] = url
    product["listing_url"] = url
    return product
