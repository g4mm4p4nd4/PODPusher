from fastapi import Depends, FastAPI

from ..common.auth import optional_user_id
from ..common.observability import register_observability
from ..control_center.service import get_settings_dashboard

app = FastAPI()
register_observability(app, service_name="settings")


@app.get("/dashboard")
async def dashboard(user_id: int | None = Depends(optional_user_id)):
    return await get_settings_dashboard(user_id)
