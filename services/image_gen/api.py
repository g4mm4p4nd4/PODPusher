from fastapi import FastAPI
from pydantic import BaseModel

from .service import generate_images, list_images, delete_image
from ..common.quotas import quota_middleware

app = FastAPI()
app.middleware("http")(quota_middleware)


class GenerateRequest(BaseModel):
    idea_id: int
    style: str
    provider_override: str | None = None


@app.post("/generate")
async def generate(data: GenerateRequest):
    return await generate_images(data.idea_id, data.style, data.provider_override)


@app.get("/")
async def list_endpoint(idea_id: int):
    return await list_images(idea_id)


@app.delete("/{image_id}")
async def delete_endpoint(image_id: int):
    return await delete_image(image_id)
