from fastapi import FastAPI
from pydantic import BaseModel
from .service import create_sku, publish_listing, create_printify_product


app = FastAPI()


class ProductList(BaseModel):
    products: list[dict]


class ProductCreate(BaseModel):
    idea_id: str
    image_ids: list[str]
    blueprint_id: str
    variants: list[str]


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


@app.post("/api/printify/products/create")
async def create_printify_product_endpoint(data: ProductCreate):
    return create_printify_product(
        data.idea_id, data.image_ids, data.blueprint_id, data.variants
    )


@app.post("/api/etsy/listings/publish")
async def publish_listing_endpoint(product: dict):
    return publish_listing(product)
