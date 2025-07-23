from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


def generate_images(idea: str) -> list[str]:
    """Return placeholder image URLs for an idea."""
    slug = idea.replace(" ", "-").lower()
    return [
        f"https://example.com/{slug}-1.png",
        f"https://example.com/{slug}-2.png",
    ]


class IdeaIn(BaseModel):
    idea: str


@app.post("/images")
async def images(payload: IdeaIn) -> dict[str, list[str]]:
    """Generate image URLs for the provided idea."""
    return {"images": generate_images(payload.idea)}
