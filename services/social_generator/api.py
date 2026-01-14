from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from .service import generate_post

app = FastAPI()


class SocialRequest(BaseModel):
    product_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    product_type: Optional[str] = None
    language: str = "en"
    include_image: bool = True


@app.post("/generate")
async def generate(data: SocialRequest):
    payload = {k: v for k, v in data.model_dump().items() if v is not None}
    result = await generate_post(payload)
    if not result:
        raise HTTPException(status_code=400, detail="Unable to generate post")
    return result
