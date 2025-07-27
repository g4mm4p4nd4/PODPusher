from fastapi import FastAPI
from pydantic import BaseModel
from .service import get_top_keywords

app = FastAPI()


class KeywordClicks(BaseModel):
    keyword: str
    clicks: int
    revenue: float


@app.get("/analytics", response_model=list[KeywordClicks])
async def analytics():
    return get_top_keywords()
