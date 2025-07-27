from fastapi import FastAPI

from .service import search_products

app = FastAPI()


@app.get("/")
async def search(
    q: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    rating_min: int | None = None,
    page: int = 1,
    page_size: int = 10,
):
    return await search_products(
        q=q,
        category=category,
        tag=tag,
        rating_min=rating_min,
        page=page,
        page_size=page_size,
    )
