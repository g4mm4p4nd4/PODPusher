from fastapi import FastAPI

from .service import get_live_trends, refresh_trends, start_scheduler

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    start_scheduler()


@app.get("/trends/live")
async def live_trends(category: str | None = None):
    return await get_live_trends(category)


@app.post("/trends/refresh")
async def refresh_endpoint():
    await refresh_trends()
    return {"status": "ok"}
