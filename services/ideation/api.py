from fastapi import FastAPI
from pydantic import BaseModel

from ..common.observability import register_observability
from .service import generate_ideas, suggest_tags

app = FastAPI()
register_observability(app, service_name="ideation")


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
