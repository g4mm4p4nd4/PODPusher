from fastapi import FastAPI
from pydantic import BaseModel
from .service import create_sku, publish_listing
from ..common.logger import init_logger, logging_middleware
from ..common.monitoring import init_monitoring


init_logger()
app = FastAPI()
app.middleware("http")(logging_middleware)
init_monitoring(app)


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
    """Backward compatible endpoint from early stubs."""
    products = create_sku(data.products)
    return {"product": products}


@app.post("/publish-listing")
async def publish_listing_legacy(product: dict):
    """Backward compatible endpoint from early stubs."""
    listing = publish_listing(product)
    return {"listing": listing.get("etsy_url"), "product": listing}
