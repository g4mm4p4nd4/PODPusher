from fastapi import FastAPI
from celery.result import AsyncResult
from ..tasks import (
    celery_app,
    fetch_trends_task,
    generate_ideas_task,
    generate_images_task,
    create_sku_task,
    publish_listing_task,
)

app = FastAPI()


@app.post("/generate")
async def generate():
    chain = (
        fetch_trends_task.s()
        | generate_ideas_task.s()
        | generate_images_task.s()
        | create_sku_task.s()
        | publish_listing_task.s()
    )
    result = chain.apply_async()
    return AsyncResult(result.id, app=celery_app).get(timeout=30)
