from fastapi import FastAPI
from pydantic import BaseModel
from .service import generate_images

app = FastAPI()


class IdeaList(BaseModel):
    ideas: list[str]


@app.post("/images")
async def images(data: IdeaList):
    return await generate_images(data.ideas)
