from fastapi import FastAPI
from .service import search_products

app = FastAPI()


@app.get("/")
async def search(
    q: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    rating_min: int | None = None,
    offset: int = 0,
    limit: int = 10,
):
    return await search_products(
        q=q,
        category=category,
        tag=tag,
        rating_min=rating_min,
        offset=offset,
        limit=limit,
    )
