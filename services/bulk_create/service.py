from __future__ import annotations

import csv
import io
import json
from typing import List, Tuple

from pydantic import BaseModel, Field, AnyHttpUrl, ValidationError

from ..integration.service import create_sku


class Variant(BaseModel):
    sku: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)


class ProductDefinition(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1)
    variants: List[Variant] = Field(..., min_length=1)
    image_urls: List[AnyHttpUrl] = Field(default_factory=list)


def parse_products_from_csv(data: str) -> Tuple[List[ProductDefinition], List[dict]]:
    items: List[ProductDefinition] = []
    errors: List[dict] = []
    reader = csv.DictReader(io.StringIO(data))
    for idx, row in enumerate(reader):
        try:
            variants = json.loads(row.get("variants", "[]"))
            images = json.loads(row.get("image_urls", "[]"))
            product = ProductDefinition(
                title=row.get("title", ""),
                description=row.get("description", ""),
                price=float(row.get("price", 0)),
                category=row.get("category", ""),
                variants=variants,
                image_urls=images,
            )
            items.append(product)
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            errors.append({"index": idx, "error": str(exc)})
    return items, errors


def parse_products_from_json(data: str) -> Tuple[List[ProductDefinition], List[dict]]:
    items: List[ProductDefinition] = []
    errors: List[dict] = []
    try:
        raw = json.loads(data)
    except json.JSONDecodeError as exc:
        return [], [{"index": 0, "error": str(exc)}]
    for idx, item in enumerate(raw):
        try:
            items.append(ProductDefinition(**item))
        except ValidationError as exc:
            errors.append({"index": idx, "error": str(exc)})
    return items, errors


def persist_products(products: List[ProductDefinition]) -> Tuple[List[dict], List[dict]]:
    created: List[dict] = []
    errors: List[dict] = []
    for idx, prod in enumerate(products):
        try:
            result = create_sku([prod.model_dump()])[0]
            created.append({"index": idx, "product": result})
        except Exception as exc:  # pragma: no cover - defensive
            errors.append({"index": idx, "error": str(exc)})
    return created, errors
