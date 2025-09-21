"""Product review API endpoints."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from ..common.localization import get_message
from ..models import Product
from .repository import fetch_latest_products, persist_product_update

app = FastAPI()


class ProductResponse(BaseModel):
    id: int
    name: str
    image_url: str
    rating: int | None = None
    tags: list[str] = Field(default_factory=list)
    flagged: bool = False

    @classmethod
    def from_model(cls, product: Product) -> "ProductResponse":
        return cls(
            id=product.id,
            name=f"Product {product.id}",
            image_url=product.image_url,
            rating=product.rating,
            tags=product.tags or [],
            flagged=bool(product.flagged),
        )


class UpdatePayload(BaseModel):
    rating: int | None = None
    tags: list[str] | None = None
    flagged: bool | None = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, value: int | None) -> int | None:
        if value is not None and not 1 <= value <= 5:
            raise ValueError("rating must be between 1 and 5")
        return value


@app.get("/review", response_model=list[ProductResponse])
async def get_products() -> list[ProductResponse]:
    products = await fetch_latest_products()
    return [ProductResponse.from_model(product) for product in products]


@app.put("/{product_id}", response_model=ProductResponse)
async def update_product_endpoint(
    request: Request,
    product_id: int,
    payload: UpdatePayload,
) -> ProductResponse:
    try:
        product = await persist_product_update(
            product_id,
            rating=payload.rating,
            tags=payload.tags,
            flagged=payload.flagged,
        )
    except ValueError as exc:  # rating validation failures
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if product is None:
        lang = request.headers.get("Accept-Language", "en")
        message = get_message(lang, "product_not_found")
        raise HTTPException(status_code=404, detail=message)

    return ProductResponse.from_model(product)
