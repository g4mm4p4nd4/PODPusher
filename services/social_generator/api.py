from fastapi import FastAPI
from pydantic import BaseModel

from .service import generate_post

app = FastAPI()


class Prompt(BaseModel):
    prompt: str


@app.post("/social/post")
async def social_post(data: Prompt):
    return await generate_post(data.prompt)
