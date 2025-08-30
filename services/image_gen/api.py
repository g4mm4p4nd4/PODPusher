from fastapi import FastAPI
from pydantic import BaseModel
from ..logging import get_logger
from ..monitoring import setup_monitoring
from .service import generate_images
from ..common.quotas import quota_middleware

app = FastAPI()
_logger = get_logger(__name__)
app.middleware("http")(quota_middleware)
setup_monitoring(app, "image_gen")


class IdeaList(BaseModel):
    ideas: list[str]


@app.post("/images")
async def images(data: IdeaList):
    return await generate_images(data.ideas)
