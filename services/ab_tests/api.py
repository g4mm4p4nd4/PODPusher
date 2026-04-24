from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime

from .service import (
    create_test,
    duplicate_test,
    end_test,
    get_metrics,
    pause_test,
    push_winner,
    record_click,
    record_impression,
)
from ..control_center.service import get_ab_dashboard
from ..models import ExperimentType

app = FastAPI()


class VariantCreate(BaseModel):
    name: str
    weight: float = 1.0


class TestCreate(BaseModel):
    name: str
    experiment_type: ExperimentType
    variants: list[VariantCreate]
    product_id: int | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None


@app.post("/")
async def create(payload: TestCreate):
    try:
        return await create_test(
            payload.name,
            payload.experiment_type,
            [v.model_dump() for v in payload.variants],
            payload.product_id,
            payload.start_time,
            payload.end_time,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/metrics")
async def metrics_all():
    return await get_metrics()


@app.get("/dashboard")
async def dashboard():
    return await get_ab_dashboard()


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


@app.post("/{test_id}/pause")
async def pause(test_id: int):
    data = await pause_test(test_id)
    if not data:
        raise HTTPException(status_code=404, detail="Test not found")
    return data


@app.post("/{test_id}/duplicate")
async def duplicate(test_id: int):
    data = await duplicate_test(test_id)
    if not data:
        raise HTTPException(status_code=404, detail="Test not found")
    return data


@app.post("/{test_id}/end")
async def end(test_id: int):
    data = await end_test(test_id)
    if not data:
        raise HTTPException(status_code=404, detail="Test not found")
    return data


@app.post("/{test_id}/push-winner")
async def winner(test_id: int):
    data = await push_winner(test_id)
    if not data:
        raise HTTPException(status_code=404, detail="Winner not found")
    return data
