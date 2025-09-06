from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from ..logging import get_logger
from ..monitoring import setup_monitoring
from .service import (
    list_notifications,
    create_notification,
    mark_read,
    start_scheduler,
)

app = FastAPI()
logger = get_logger(__name__)
setup_monitoring(app)


@app.on_event("startup")
async def start() -> None:
    start_scheduler()


class NotificationCreate(BaseModel):
    message: str
    type: str = "info"
    user_id: int | None = None


@app.get("/")
async def get_notifications(x_user_id: str = Header(..., alias="X-User-Id")):
    return await list_notifications(int(x_user_id))


@app.post("/")
async def create_notification_endpoint(
    payload: NotificationCreate,
    x_user_id: str = Header(None, alias="X-User-Id"),
):
    user_id = payload.user_id or int(x_user_id)
    return await create_notification(user_id, payload.message, payload.type)


@app.put("/{notification_id}/read")
async def mark_read_endpoint(notification_id: int):
    notif = await mark_read(notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif
