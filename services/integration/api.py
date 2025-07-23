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
