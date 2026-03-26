from __future__ import annotations

import asyncio
import os
from typing import Any
from uuid import uuid4

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from packages.broker import EventBroker
from ..common.product_pipeline import assemble_products

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
IDEATION_URL = os.getenv("IDEATION_URL", "http://ideation:8002")
IMAGE_URL = os.getenv("IMAGE_URL", "http://image_gen:8003")
INTEGRATION_URL = os.getenv("INTEGRATION_URL", "http://integration:8004")
NOTIFICATIONS_URL = os.getenv("NOTIFICATIONS_URL", "http://notifications:8005")

TREND_SIGNALS_STREAM = "trend_signals"
IDEAS_READY_STREAM = "ideas_ready"
IMAGES_READY_STREAM = "images_ready"
PRODUCTS_READY_STREAM = "products_ready"
LISTINGS_READY_STREAM = "listings_ready"

broker = EventBroker(REDIS_URL)
scheduler = AsyncIOScheduler()
_consumer_tasks: list[asyncio.Task[Any]] = []
_scheduled_jobs: dict[str, dict[str, Any]] = {}


def _auth_headers(user_id: int) -> dict[str, str]:
    return {"X-User-Id": str(user_id)}


def _service_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


async def _post_json(
    base_url: str,
    path: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
) -> Any:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            _service_url(base_url, path),
            json=payload,
            headers=headers,
        )
    response.raise_for_status()
    return response.json()


async def _notify(user_id: int, message: str) -> None:
    try:
        await _post_json(
            NOTIFICATIONS_URL,
            "/",
            {"message": message, "type": "info"},
            headers=_auth_headers(user_id),
        )
    except httpx.HTTPError:
        # Notifications are side effects; do not poison the pipeline if they fail.
        return


def _valid_user_id(message: dict[str, Any]) -> int | None:
    user_id = message.get("user_id")
    if isinstance(user_id, bool):
        return None
    if isinstance(user_id, int):
        return user_id
    if isinstance(user_id, str) and user_id.isdigit():
        return int(user_id)
    return None


async def publish_trend_signal(
    *,
    user_id: int,
    trend: str,
    source: str = "manual",
    auto: bool = False,
) -> dict[str, Any]:
    event = {
        "user_id": user_id,
        "trend": trend,
        "source": source,
        "auto": auto,
    }
    await broker.publish(TREND_SIGNALS_STREAM, event)
    return event


async def _publish_scheduled_trend_signal(
    *,
    job_id: str,
    user_id: int,
    trend: str,
    source: str,
) -> None:
    await publish_trend_signal(user_id=user_id, trend=trend, source=source, auto=True)


def register_periodic_trend_signal(
    *,
    user_id: int,
    trend: str,
    interval_seconds: int,
    source: str = "scheduled",
) -> dict[str, Any]:
    if user_id <= 0:
        raise ValueError("user_id must be positive")
    if not trend.strip():
        raise ValueError("trend must be provided")
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")

    if not scheduler.running:
        scheduler.start()

    job_id = f"trend-{user_id}-{uuid4().hex[:10]}"
    scheduler.add_job(
        _publish_scheduled_trend_signal,
        "interval",
        seconds=interval_seconds,
        id=job_id,
        kwargs={
            "job_id": job_id,
            "user_id": user_id,
            "trend": trend,
            "source": source,
        },
        replace_existing=True,
    )
    schedule = {
        "job_id": job_id,
        "user_id": user_id,
        "trend": trend,
        "interval_seconds": interval_seconds,
        "source": source,
    }
    _scheduled_jobs[job_id] = schedule
    return schedule


def list_registered_schedules(*, user_id: int | None = None) -> list[dict[str, Any]]:
    schedules = list(_scheduled_jobs.values())
    if user_id is None:
        return schedules
    return [job for job in schedules if job["user_id"] == user_id]


def remove_periodic_trend_signal(*, job_id: str, user_id: int) -> bool:
    schedule = _scheduled_jobs.get(job_id)
    if not schedule or schedule["user_id"] != user_id:
        return False
    if scheduler.get_job(job_id) is not None:
        scheduler.remove_job(job_id)
    _scheduled_jobs.pop(job_id, None)
    return True


async def handle_trend(message: dict[str, Any]) -> None:
    user_id = _valid_user_id(message)
    trend = str(message.get("trend", "")).strip()
    if user_id is None or not trend:
        return

    ideas = await _post_json(IDEATION_URL, "/ideas", {"trends": [trend]})
    await broker.publish(
        IDEAS_READY_STREAM,
        {
            "user_id": user_id,
            "trend": trend,
            "source": message.get("source", "manual"),
            "auto": bool(message.get("auto", False)),
            "ideas": ideas,
        },
    )
    await _notify(user_id, "Ideas generated")


async def handle_ideas(message: dict[str, Any]) -> None:
    user_id = _valid_user_id(message)
    ideas = message.get("ideas")
    if user_id is None or not isinstance(ideas, list) or not ideas:
        return

    images: list[dict[str, Any]] = []
    headers = _auth_headers(user_id)
    for idea in ideas:
        if not isinstance(idea, dict) or idea.get("id") is None:
            continue
        generated = await _post_json(
            IMAGE_URL,
            "/generate",
            {
                "idea_id": int(idea["id"]),
                "style": idea.get("style", "default"),
                "provider_override": idea.get("provider_override"),
            },
            headers=headers,
        )
        if isinstance(generated, list):
            images.extend(generated)

    if not images:
        return

    await broker.publish(
        IMAGES_READY_STREAM,
        {
            "user_id": user_id,
            "trend": message.get("trend"),
            "source": message.get("source", "manual"),
            "auto": bool(message.get("auto", False)),
            "ideas": ideas,
            "images": images,
        },
    )
    await _notify(user_id, "Images generated")


async def handle_images(message: dict[str, Any]) -> None:
    user_id = _valid_user_id(message)
    ideas = message.get("ideas")
    images = message.get("images")
    if user_id is None or not isinstance(ideas, list) or not isinstance(images, list):
        return

    product_inputs = assemble_products(ideas, images)
    if not product_inputs:
        return

    products = await _post_json(
        INTEGRATION_URL,
        "/sku",
        {"products": product_inputs},
        headers=_auth_headers(user_id),
    )

    await broker.publish(
        PRODUCTS_READY_STREAM,
        {
            "user_id": user_id,
            "trend": message.get("trend"),
            "source": message.get("source", "manual"),
            "auto": bool(message.get("auto", False)),
            "products": products,
        },
    )
    await _notify(user_id, "Products created")


async def handle_products(message: dict[str, Any]) -> None:
    user_id = _valid_user_id(message)
    products = message.get("products")
    if user_id is None or not isinstance(products, list) or not products:
        return

    first_product = products[0]
    if not isinstance(first_product, dict):
        return

    listing = await _post_json(
        INTEGRATION_URL,
        "/listing",
        first_product,
        headers=_auth_headers(user_id),
    )

    await broker.publish(
        LISTINGS_READY_STREAM,
        {
            "user_id": user_id,
            "trend": message.get("trend"),
            "source": message.get("source", "manual"),
            "auto": bool(message.get("auto", False)),
            "product": first_product,
            "listing": listing,
        },
    )
    await _notify(user_id, "Listing published")


async def start() -> None:
    if _consumer_tasks:
        return
    if not scheduler.running:
        scheduler.start()
    _consumer_tasks.extend(
        [
            asyncio.create_task(
                broker.consume(TREND_SIGNALS_STREAM, "trend-signals", "orchestrator-trend", handle_trend)
            ),
            asyncio.create_task(
                broker.consume(IDEAS_READY_STREAM, "ideas-ready", "orchestrator-ideas", handle_ideas)
            ),
            asyncio.create_task(
                broker.consume(IMAGES_READY_STREAM, "images-ready", "orchestrator-images", handle_images)
            ),
            asyncio.create_task(
                broker.consume(PRODUCTS_READY_STREAM, "products-ready", "orchestrator-products", handle_products)
            ),
        ]
    )


async def stop() -> None:
    global scheduler
    while _consumer_tasks:
        task = _consumer_tasks.pop()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    if scheduler.running:
        scheduler.remove_all_jobs()
        scheduler.shutdown(wait=False)
    _scheduled_jobs.clear()
    scheduler = AsyncIOScheduler()
    await broker.close()
