from fastapi import FastAPI
from pydantic import BaseModel
from .service import generate_ideas, suggest_tags
from ..common.logger import init_logger, logging_middleware
from ..common.monitoring import init_monitoring

init_logger()
app = FastAPI()
app.middleware("http")(logging_middleware)
init_monitoring(app)


class TrendList(BaseModel):
    trends: list[str]


class ListingData(BaseModel):
    title: str
    description: str


@app.post("/ideas")
async def ideas(data: TrendList):
    return await generate_ideas(data.trends)


@app.post("/suggest-tags")
async def tags(data: ListingData):
    return await suggest_tags(data.title, data.description)
