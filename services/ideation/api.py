from fastapi import FastAPI
from pydantic import BaseModel
from .service import generate_ideas, suggest_tags

app = FastAPI()


class TrendList(BaseModel):
    trends: list[str]


class DescriptionPayload(BaseModel):
    description: str


@app.post("/ideas")
async def ideas(data: TrendList):
    return await generate_ideas(data.trends)


@app.post("/suggest-tags")
async def suggest_tags_endpoint(data: DescriptionPayload):
    return await suggest_tags(data.description)
