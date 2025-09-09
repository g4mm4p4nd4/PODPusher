from fastapi import FastAPI
from pydantic import BaseModel

from .service import generate_images
from ..common.quotas import quota_middleware

app = FastAPI()
app.middleware("http")(quota_middleware)


class ImageRequest(BaseModel):
    idea_id: int
    style: str
    provider_override: str | None = None


@app.post("/generate")
async def generate(req: ImageRequest):
    urls = await generate_images(req.idea_id, req.style, req.provider_override)
    return {"urls": urls}
