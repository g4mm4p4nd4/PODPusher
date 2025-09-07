from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime

from .service import (
    create_test,
    get_metrics,
    record_click,
    record_impression,
)
from ..models import ExperimentType
from ..common.monitoring import setup_observability

app = FastAPI()
setup_observability(app)


class VariantCreate(BaseModel):
    name: str
    weight: float = 1.0


class TestCreate(BaseModel):
    name: str
    experiment_type: ExperimentType
    variants: list[VariantCreate]
    start_time: datetime | None = None
    end_time: datetime | None = None


@app.post("/")
async def create(payload: TestCreate):
    try:
        return await create_test(
            payload.name,
            payload.experiment_type,
            [v.model_dump() for v in payload.variants],
            payload.start_time,
            payload.end_time,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/ab_metrics")
async def metrics_all():
    return await get_metrics()


@app.get("/{test_id}/ab_metrics")
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
