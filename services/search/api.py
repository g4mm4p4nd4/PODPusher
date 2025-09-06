from fastapi import FastAPI
from pydantic import BaseModel
from .service import search_products
from ..common.logger import init_logger, logging_middleware
from ..common.monitoring import init_monitoring


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


init_logger()
app = FastAPI()
app.middleware("http")(logging_middleware)
init_monitoring(app)


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
