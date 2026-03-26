from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .service import delete_image, generate_image_for_idea, generate_images, list_images
from ..common.observability import register_observability
from ..common.quotas import quota_middleware

app = FastAPI()
register_observability(app, service_name="image_gen")
app.middleware("http")(quota_middleware)


class IdeaList(BaseModel):
    ideas: list[str]


class GenerateRequest(BaseModel):
    idea_id: int
    style: str = "default"
    provider_override: str | None = None


@app.post("/images")
async def images(data: IdeaList):
    return await generate_images(data.ideas)


@app.post("/generate")
async def generate(data: GenerateRequest):
    images = await generate_image_for_idea(
        idea_id=data.idea_id,
        style=data.style,
        provider_override=data.provider_override,
    )
    if not images:
        raise HTTPException(status_code=404, detail="Idea not found")
    return images


@app.get("/")
async def list_endpoint(idea_id: int):
    return await list_images(idea_id)


@app.delete("/{image_id}")
async def delete_endpoint(image_id: int):
    deleted = await delete_image(image_id)
    if deleted["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Image not found")
    return deleted
