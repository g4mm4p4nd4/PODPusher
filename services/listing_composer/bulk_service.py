from __future__ import annotations

import asyncio
import csv
import io
from typing import List, Tuple

from pydantic import BaseModel, Field, ValidationError, root_validator

from ..integration.service import publish_listing


class ProductDefinition(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    base_product_type: str = Field(..., min_length=1)
    variants: List[str] = Field(min_length=1)
    tags: List[str] | None = None
    categories: List[str] | None = None
    images: List[str] | None = None

    @root_validator(pre=True)
    def split_fields(cls, values):  # type: ignore[override]
        for field in ["variants", "tags", "categories", "images"]:
            if isinstance(values.get(field), str):
                values[field] = [
                    v.strip() for v in values[field].split(";") if v.strip()
                ]
        return values


class BulkResult(BaseModel):
    created: List[int] = []
    errors: List[dict] = []


def parse_csv(data: bytes) -> List[ProductDefinition]:
    try:
        text = data.decode()
    except Exception as exc:  # pragma: no cover - decode error
        raise ValueError("invalid encoding") from exc
    reader = csv.DictReader(io.StringIO(text))
    products: List[ProductDefinition] = []
    for row in reader:
        try:
            products.append(ProductDefinition(**row))
        except ValidationError as exc:
            raise ValueError(str(exc))
    return products


async def create_listings(products: List[ProductDefinition]) -> BulkResult:
    async def process(prod: ProductDefinition) -> Tuple[int | None, str | None]:
        try:
            listing = await asyncio.to_thread(publish_listing, prod.model_dump())
            return listing.get("id", 0), None
        except Exception as exc:  # pragma: no cover - integration failure
            return None, str(exc)

    tasks = [process(p) for p in products]
    results = await asyncio.gather(*tasks)
    created: List[int] = []
    errors: List[dict] = []
    for idx, (listing_id, err) in enumerate(results, start=1):
        if listing_id is not None:
            created.append(listing_id)
        else:
            errors.append({"row": idx, "error": err or "unknown error"})
    return BulkResult(created=created, errors=errors)
