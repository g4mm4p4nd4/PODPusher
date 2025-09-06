from fastapi import FastAPI
from pydantic import BaseModel
from .service import generate_images
from ..common.quotas import quota_middleware
from ..common.logger import init_logger, logging_middleware
from ..common.monitoring import init_monitoring

init_logger()
app = FastAPI()
app.middleware("http")(logging_middleware)
app.middleware("http")(quota_middleware)
init_monitoring(app)


class IdeaList(BaseModel):
    ideas: list[str]


@app.post("/images")
async def images(data: IdeaList):
    return await generate_images(data.ideas)
