from fastapi import FastAPI
from .service import fetch_trends
from ..tasks import celery_app

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    celery_app.send_task("services.tasks.fetch_trends_task")


@app.get("/trends")
async def get_trends():
    return await fetch_trends()
