from fastapi import FastAPI
from pydantic import BaseModel
from .service import generate_ideas

app = FastAPI()


class TrendList(BaseModel):
    trends: list[str]


@app.post("/ideas")
async def ideas(data: TrendList):
    return await generate_ideas(data.trends)
