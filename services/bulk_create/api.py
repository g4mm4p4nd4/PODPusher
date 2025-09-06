from __future__ import annotations

from typing import List
import json

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from .service import (
    ProductDefinition,
    parse_products_from_csv,
    parse_products_from_json,
    persist_products,
)


class BulkCreateResponse(BaseModel):
    created: List[dict]
    errors: List[dict]


app = FastAPI()


@app.post("", response_model=BulkCreateResponse)
async def bulk_create(request: Request) -> BulkCreateResponse:
    content_type = request.headers.get("content-type", "")
    items: List[ProductDefinition] = []
    errors: List[dict] = []

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file")
        if upload is None:
            raise HTTPException(status_code=400, detail="no products provided")
        content = (await upload.read()).decode("utf-8")
        filename = getattr(upload, "filename", "")
        if filename.lower().endswith(".csv"):
            items, errors = parse_products_from_csv(content)
        elif filename.lower().endswith(".json"):
            items, errors = parse_products_from_json(content)
        else:
            raise HTTPException(status_code=400, detail="unsupported file type")
    else:
        try:
            products = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="no products provided")
        items, parse_errors = parse_products_from_json(json.dumps(products))
        errors.extend(parse_errors)

    created, persist_errors = persist_products(items)
    errors.extend(persist_errors)
    return BulkCreateResponse(created=created, errors=errors)
