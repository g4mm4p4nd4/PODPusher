from fastapi import Depends, FastAPI
from pydantic import BaseModel

from ..common.auth import optional_user_id
from ..common.observability import register_observability
from ..control_center.service import get_seasonal_events, save_seasonal_event

app = FastAPI()
register_observability(app, service_name="seasonal")


class SaveEventRequest(BaseModel):
    name: str


@app.get("/events")
async def events(
    user_id: int | None = Depends(optional_user_id),
    date_from: str | None = None,
    date_to: str | None = None,
    store: str | None = None,
    region: str = "US",
    country: str | None = None,
    language: str = "en",
    marketplace: str = "etsy",
    category: str = "all",
    search: str | None = None,
    horizon_months: int = 6,
):
    return await get_seasonal_events(
        user_id,
        region=country or region,
        language=language,
        marketplace=marketplace,
        category=category,
        horizon_months=horizon_months,
        date_from=date_from,
        date_to=date_to,
        store=store,
        search=search,
    )


@app.post("/events/save")
async def save_event(
    payload: SaveEventRequest,
    user_id: int | None = Depends(optional_user_id),
):
    return await save_seasonal_event(user_id, payload.name)
