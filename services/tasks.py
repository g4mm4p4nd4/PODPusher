import os
from celery import Celery
from .trend_scraper.service import fetch_trends
from .ideation.service import generate_ideas
from .image_gen.service import generate_images
from .integration.service import create_sku, publish_listing

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("worker", broker=CELERY_BROKER_URL, backend=CELERY_BROKER_URL)

celery_app.conf.beat_schedule = {
    "refresh_trends": {"task": "services.tasks.fetch_trends_task", "schedule": 21600}
}


@celery_app.task
def fetch_trends_task():
    return fetch_trends()


@celery_app.task
def generate_ideas_task(trends):
    return generate_ideas(trends)


@celery_app.task
def generate_images_task(ideas):
    return generate_images(ideas)


@celery_app.task
def create_sku_task(images):
    return create_sku(images)


@celery_app.task
def publish_listing_task(product):
    return publish_listing(product)
