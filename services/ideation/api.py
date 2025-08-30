from fastapi import FastAPI
from pydantic import BaseModel
from ..logging import get_logger
from ..monitoring import setup_monitoring
from .service import generate_ideas, suggest_tags

app = FastAPI()
_logger = get_logger(__name__)
setup_monitoring(app, "ideation")


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
