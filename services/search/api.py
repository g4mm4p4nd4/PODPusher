from typing import Any

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from ..common.auth import optional_user_id
from ..common.observability import register_observability
from ..control_center.service import (
    add_watchlist_item,
    get_search_insights,
    save_search,
)
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


class SaveSearchRequest(BaseModel):
    name: str | None = None
    query: str = ""
    filters: dict[str, Any] = Field(default_factory=dict)
    result_count: int = 0


class WatchlistRequest(BaseModel):
    item_type: str = "product"
    name: str
    context: dict[str, Any] = Field(default_factory=dict)


app = FastAPI()
register_observability(app, service_name="search")


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


@app.get("/insights")
async def insights(
    q: str | None = None,
    category: str | None = None,
    marketplace: str = "etsy",
    season: str | None = None,
    niche: str | None = None,
    user_id: int | None = Depends(optional_user_id),
):
    return await get_search_insights(
        user_id,
        q=q,
        category=category,
        marketplace=marketplace,
        season=season,
        niche=niche,
    )


@app.post("/saved")
async def create_saved_search(
    payload: SaveSearchRequest,
    user_id: int | None = Depends(optional_user_id),
):
    return await save_search(user_id, payload.model_dump())


@app.post("/watchlist")
async def create_watchlist_item(
    payload: WatchlistRequest,
    user_id: int | None = Depends(optional_user_id),
):
    return await add_watchlist_item(user_id, payload.model_dump())
