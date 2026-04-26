from fastapi import Depends, FastAPI

from ..common.auth import optional_user_id
from ..common.observability import register_observability
from ..control_center.service import get_overview_dashboard

app = FastAPI()
register_observability(app, service_name="dashboard")


@app.get("/overview")
async def overview(
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
    return await get_overview_dashboard(
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
