from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .service import (
    create_test,
    get_metrics,
    record_click,
    record_impression,
)


app = FastAPI()


class TestCreate(BaseModel):
    name: str
    variants: list[str]


@app.post("/")
async def create(payload: TestCreate):
    return await create_test(payload.name, payload.variants)


@app.get("/metrics")
async def metrics_all():
    return await get_metrics()


@app.get("/{test_id}/metrics")
async def metrics(test_id: int):
    return await get_metrics(test_id)


@app.post("/{variant_id}/click")
async def click(variant_id: int):
    data = await record_click(variant_id)
    if not data:
        raise HTTPException(status_code=404, detail="Variant not found")
    return data


@app.post("/{variant_id}/impression")
async def impression(variant_id: int):
    data = await record_impression(variant_id)
    if not data:
        raise HTTPException(status_code=404, detail="Variant not found")
    return data
