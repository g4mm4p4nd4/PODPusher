from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .service import list_products, update_product

app = FastAPI()


class UpdatePayload(BaseModel):
    rating: int | None = None
    tags: list[str] | None = None
    flagged: bool | None = None


@app.get("/")
async def get_products():
    return await list_products()


@app.post("/{product_id}")
async def update_product_endpoint(product_id: int, payload: UpdatePayload):
    product = await update_product(
        product_id,
        rating=payload.rating,
        tags=payload.tags,
        flagged=payload.flagged,
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
