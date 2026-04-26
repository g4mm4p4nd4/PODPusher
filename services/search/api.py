from typing import Any

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from ..common.auth import optional_user_id
from ..common.observability import register_observability
from ..control_center.service import (
    add_watchlist_item,
    generate_search_tags,
    get_search_insights,
    save_search_state,
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


class SearchStateRequest(BaseModel):
    name: str | None = None
    query: str = ""
    search: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    selected_ids: list[int] = Field(default_factory=list)
    view: str = "results"
    sort: str = "relevance"
    result_count: int = 0


class GenerateTagsRequest(BaseModel):
    name: str | None = None
    query: str | None = None
    keyword: str | None = None
    niche: str | None = None
    category: str | None = None
    seed_tags: list[str] = Field(default_factory=list)
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
    search: str | None = None,
    category: str | None = None,
    marketplace: str = "etsy",
    country: str = "US",
    language: str = "en",
    store: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    season: str | None = None,
    niche: str | None = None,
    rating_min: float | None = None,
    rating_max: float | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    user_id: int | None = Depends(optional_user_id),
):
    return await get_search_insights(
        user_id,
        q=q,
        category=category,
        marketplace=marketplace,
        country=country,
        language=language,
        store=store,
        date_from=date_from,
        date_to=date_to,
        season=season,
        niche=niche,
        search=search,
        rating_min=rating_min,
        rating_max=rating_max,
        price_min=price_min,
        price_max=price_max,
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


@app.post("/state")
async def create_search_state(
    payload: SearchStateRequest,
    user_id: int | None = Depends(optional_user_id),
):
    return await save_search_state(user_id, payload.model_dump())


@app.post("/generate-tags")
async def create_generated_tags(
    payload: GenerateTagsRequest,
    user_id: int | None = Depends(optional_user_id),
):
    return await generate_search_tags(user_id, payload.model_dump())
