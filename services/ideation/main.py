from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


def generate_ideas(trends: list[str]) -> list[str]:
    """Create simple product ideas from trends."""
    return [f"Graphic tee inspired by {trend.lstrip('#')}" for trend in trends]


class TrendsIn(BaseModel):
    trends: list[str]


@app.post("/ideas")
async def ideas(payload: TrendsIn) -> dict[str, list[str]]:
    """Return product ideas based on provided trends."""
    return {"ideas": generate_ideas(payload.trends)}
