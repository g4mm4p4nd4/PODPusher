from fastapi import FastAPI
from pydantic import BaseModel
from ..logging import get_logger
from ..monitoring import setup_monitoring
from .service import generate_post

app = FastAPI()
_logger = get_logger(__name__)
setup_monitoring(app, "social_generator")


class Prompt(BaseModel):
    prompt: str


@app.post("/social/post")
async def social_post(data: Prompt):
    return await generate_post(data.prompt)
