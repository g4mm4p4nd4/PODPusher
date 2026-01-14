import asyncio
import os
from typing import Any, Callable

from celery import Celery

from .trend_scraper.service import fetch_trends
from .ideation.service import generate_ideas
from .image_gen.service import generate_images
from .integration.service import create_sku, publish_listing
from .social_generator.service import generate_post

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("worker", broker=CELERY_BROKER_URL, backend=CELERY_BROKER_URL)

celery_app.conf.beat_schedule = {
    "refresh_trends": {"task": "services.tasks.fetch_trends_task", "schedule": 21600}
}


def _execute_service(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Execute a possibly-async service and return its concrete result."""

    result = func(*args, **kwargs)
    if asyncio.iscoroutine(result):
        return asyncio.run(result)
    return result


@celery_app.task
def fetch_trends_task(category: str | None = None):
    return asyncio.run(fetch_trends(category))


@celery_app.task
def generate_ideas_task(trends):
    return asyncio.run(generate_ideas(trends))


@celery_app.task
def generate_images_task(ideas):
    return asyncio.run(generate_images(ideas))


@celery_app.task
def create_sku_task(images):
    return _execute_service(create_sku, images)


@celery_app.task
def publish_listing_task(product):
    return _execute_service(publish_listing, product)


@celery_app.task
def generate_social_post_task(payload: dict[str, object]):
    """Celery task to create social media content."""
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a dictionary")
    return asyncio.run(generate_post(payload))
