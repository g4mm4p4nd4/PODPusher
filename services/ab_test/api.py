from fastapi import FastAPI
from pydantic import BaseModel

from .service import create_test, get_metrics, record_click, record_impression

app = FastAPI()


class VariantInput(BaseModel):
    title: str
    description: str
    variant_a: str
    variant_b: str
    tags_a: list[str] | None = None
    tags_b: list[str] | None = None


@app.post("/api/ab_tests")
async def create_ab_test(payload: VariantInput):
    test_id = await create_test(
        payload.title,
        payload.description,
        payload.variant_a,
        payload.variant_b,
        payload.tags_a,
        payload.tags_b,
    )
    return {"id": test_id}


@app.get("/api/ab_tests/{test_id}")
async def get_ab_test_metrics(test_id: int):
    return await get_metrics(test_id)


@app.post("/api/ab_tests/{test_id}/record_click")
async def record_click_endpoint(test_id: int, variant: str):
    await record_click(test_id, variant)
    return {"status": "ok"}


@app.post("/api/ab_tests/{test_id}/record_impression")
async def record_impression_endpoint(test_id: int, variant: str):
    await record_impression(test_id, variant)
    return {"status": "ok"}
