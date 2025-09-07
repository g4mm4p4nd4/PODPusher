from fastapi import FastAPI
from pydantic import BaseModel
from .service import create_sku, publish_listing


app = FastAPI()


class ProductList(BaseModel):
    products: list[dict]


@app.post("/sku")
async def sku(data: ProductList):
    return create_sku(data.products)


@app.post("/listing")
async def listing(product: dict):
    return publish_listing(product)


@app.post("/create-sku")
async def create_sku_legacy(data: ProductList):
    """Legacy endpoint for backward compatibility."""
    products = create_sku(data.products)
    return {"product": products}


@app.post("/publish-listing")
async def publish_listing_legacy(product: dict):
    """Legacy endpoint for backward compatibility."""
    listing = publish_listing(product)
    return {"listing": listing.get("etsy_url"), "product": listing}
