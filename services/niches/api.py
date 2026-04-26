from typing import Any

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from ..common.auth import optional_user_id
from ..common.observability import register_observability
from ..control_center.service import (
    get_brand_profile,
    get_niche_suggestions,
    save_niche,
    upsert_brand_profile,
)

app = FastAPI()
register_observability(app, service_name="niches")


class BrandProfileRequest(BaseModel):
    name: str | None = None
    tone: str | None = None
    audience: str | None = None
    interests: list[str] | None = None
    banned_topics: list[str] | None = None
    preferred_products: list[str] | None = None
    region: str | None = None
    language: str | None = None
    active: bool | None = None


class SaveNicheRequest(BaseModel):
    niche: str
    score: int = 0
    context: dict[str, Any] | None = None


@app.get("/profile")
async def profile(user_id: int | None = Depends(optional_user_id)):
    return await get_brand_profile(user_id)


@app.post("/profile")
async def save_profile(
    payload: BrandProfileRequest,
    user_id: int | None = Depends(optional_user_id),
):
    return await upsert_brand_profile(
        user_id,
        {
            key: value
            for key, value in payload.model_dump().items()
            if value is not None
        },
    )


@app.get("/suggestions")
async def suggestions(
    user_id: int | None = Depends(optional_user_id),
    date_from: str | None = None,
    date_to: str | None = None,
    store: str | None = None,
    marketplace: str = "etsy",
    country: str = "US",
    language: str = "en",
    category: str | None = None,
    search: str | None = None,
):
    return await get_niche_suggestions(
        user_id,
        date_from=date_from,
        date_to=date_to,
        store=store,
        marketplace=marketplace,
        country=country,
        language=language,
        category=category,
        search=search,
    )


@app.post("/saved")
async def save(
    payload: SaveNicheRequest, user_id: int | None = Depends(optional_user_id)
):
    return await save_niche(user_id, payload.niche, payload.score, payload.context)
