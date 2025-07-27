from fastapi import FastAPI, Header
from pydantic import BaseModel
from .service import (
    create_notification,
    list_notifications,
    mark_read,
    start_scheduler,
)

app = FastAPI()


class NotificationCreate(BaseModel):
    message: str


@app.on_event("startup")
async def startup_event() -> None:
    await start_scheduler()


@app.get("/")
async def get_notifications(x_user_id: str = Header(..., alias="X-User-Id")):
    return [n.dict() for n in await list_notifications(int(x_user_id))]


@app.post("/")
async def post_notification(
    payload: NotificationCreate, x_user_id: str = Header(..., alias="X-User-Id")
):
    notif = await create_notification(int(x_user_id), payload.message)
    return notif.dict()


@app.put("/{notification_id}/read")
async def mark_notification_read(notification_id: int):
    await mark_read(notification_id)
    return {"status": "ok"}
