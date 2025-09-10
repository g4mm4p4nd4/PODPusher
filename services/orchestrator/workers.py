import asyncio
import os
from typing import Dict

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from packages.broker import EventBroker

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
IDEATION_URL = os.getenv("IDEATION_URL", "http://ideation:8002")
IMAGE_URL = os.getenv("IMAGE_URL", "http://image_gen:8003")
PRODUCT_URL = os.getenv("PRODUCT_URL", "http://integration:8004")
LISTING_URL = os.getenv("LISTING_URL", "http://integration:8004")
NOTIFICATIONS_URL = os.getenv("NOTIFICATIONS_URL", "http://notifications:8005")

broker = EventBroker(REDIS_URL)
scheduler = AsyncIOScheduler()
consumers: list[asyncio.Task] = []


async def notify(message: str) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(f"{NOTIFICATIONS_URL}/", json={"message": message})


async def call_ideation_service(trend: str) -> Dict[str, str]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{IDEATION_URL}/", json={"trend": trend})
    return resp.json()


async def call_image_service(payload: Dict[str, str]) -> Dict[str, str]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{IMAGE_URL}/", json=payload)
    return resp.json()


async def call_product_service(payload: Dict[str, str]) -> Dict[str, str]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{PRODUCT_URL}/", json=payload)
    return resp.json()


async def call_listing_service(payload: Dict[str, str]) -> Dict[str, str]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{LISTING_URL}/", json=payload)
    return resp.json()


async def handle_trend(message: Dict[str, str]) -> None:
    ideas = await call_ideation_service(message["trend"])  # type: ignore[index]
    await broker.publish("ideas_ready", ideas)
    await notify("Ideas generated")


async def handle_idea(message: Dict[str, str]) -> None:
    images = await call_image_service(message)
    await broker.publish("images_ready", images)
    await notify("Images generated")


async def handle_image(message: Dict[str, str]) -> None:
    product = await call_product_service(message)
    await broker.publish("products_ready", product)
    await notify("Product created")


async def handle_product(message: Dict[str, str]) -> None:
    listing = await call_listing_service(message)
    await broker.publish("listings_ready", listing)
    await notify("Listing published")


async def restock_check() -> None:
    await notify("Restock check complete")


async def expired_listing_cleanup() -> None:
    await notify("Expired listing cleanup complete")


async def schedule_jobs() -> None:
    restock = int(os.getenv("RESTOCK_INTERVAL", "86400"))
    cleanup = int(os.getenv("CLEANUP_INTERVAL", "86400"))
    trend = int(os.getenv("TREND_INTERVAL", "3600"))
    scheduler.add_job(restock_check, "interval", seconds=restock)
    scheduler.add_job(expired_listing_cleanup, "interval", seconds=cleanup)
    scheduler.add_job(lambda: broker.publish("trend_signals", {"auto": "1"}), "interval", seconds=trend)
    scheduler.start()


async def start() -> None:
    consumers.extend(
        [
            asyncio.create_task(broker.consume("trend_signals", "trend", "c1", handle_trend)),
            asyncio.create_task(broker.consume("ideas_ready", "ideas", "c2", handle_idea)),
            asyncio.create_task(broker.consume("images_ready", "images", "c3", handle_image)),
            asyncio.create_task(broker.consume("products_ready", "products", "c4", handle_product)),
        ]
    )
    await schedule_jobs()


async def stop() -> None:
    scheduler.shutdown()
    for task in consumers:
        task.cancel()
    await broker.close()
