from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .service import create_test, get_metrics, record_click

app = FastAPI()


class VariantInput(BaseModel):
    title: str
    description: str
    tags: list[str] = []


class CreateRequest(BaseModel):
    variant_a: VariantInput
    variant_b: VariantInput


class ClickRequest(BaseModel):
    variant: str


@app.post("/", response_model=dict)
async def create_ab_test(req: CreateRequest):
    test_id = await create_test(req.variant_a.model_dump(), req.variant_b.model_dump())
    return {"id": test_id}


@app.get("/{test_id}")
async def get_ab_test(test_id: int):
    data = await get_metrics(test_id)
    if not data:
        raise HTTPException(status_code=404, detail="Test not found")
    return data


@app.post("/{test_id}/record_click")
async def record_click_endpoint(test_id: int, click: ClickRequest):
    await record_click(test_id, click.variant)
    return {"status": "ok"}
