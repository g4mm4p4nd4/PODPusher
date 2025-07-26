from fastapi import FastAPI
from pydantic import BaseModel
from .service import generate_images
from ..common.quotas import quota_middleware

app = FastAPI()
app.middleware("http")(quota_middleware)


class IdeaList(BaseModel):
    ideas: list[str]


@app.post("/images")
async def images(data: IdeaList):
    return await generate_images(data.ideas)
