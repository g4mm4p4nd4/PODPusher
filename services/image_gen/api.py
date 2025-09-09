from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .service import generate_images, list_images, delete_image
from ..common.quotas import quota_middleware


class GeneratePayload(BaseModel):
    idea_id: int
    style: str
    provider_override: str | None = None
    model_version: str | None = None


app = FastAPI()
app.middleware("http")(quota_middleware)


@app.post("/generate")
async def generate_endpoint(payload: GeneratePayload):
    return await generate_images(
        payload.idea_id,
        payload.style,
        payload.provider_override,
        payload.model_version,
    )


@app.get("/{idea_id}")
async def list_endpoint(idea_id: int):
    return await list_images(idea_id)


@app.delete("/{image_id}")
async def delete_endpoint(image_id: int):
    ok = await delete_image(image_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"status": "deleted"}
