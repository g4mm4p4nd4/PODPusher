from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .service import list_reviews, update_review

app = FastAPI()


class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    tags: Optional[List[str]] = None
    flagged: Optional[bool] = None


@app.get("/images/review")
async def get_reviews():
    return await list_reviews()


@app.post("/images/review/{product_id}")
async def post_review(product_id: int, data: ReviewUpdate):
    product = await update_review(product_id, data.rating, data.tags, data.flagged)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
