from fastapi import FastAPI
from pydantic import BaseModel
from ..logging import get_logger
from ..monitoring import setup_monitoring
from .service import search_products


class SearchItem(BaseModel):
    id: int
    name: str
    description: str | None = None
    image_url: str
    rating: int | None = None
    tags: list[str] = []
    category: str


class SearchResponse(BaseModel):
    items: list[SearchItem]
    total: int
    page: int
    page_size: int


app = FastAPI()
_logger = get_logger(__name__)
setup_monitoring(app, "search")


@app.get("/", response_model=SearchResponse)
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
