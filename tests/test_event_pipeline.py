import asyncio

import fakeredis.aioredis
import pytest

from packages.broker import EventBroker
from services.orchestrator import workers


@pytest.mark.asyncio
async def test_pipeline(monkeypatch) -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    broker = EventBroker(redis=redis)
    monkeypatch.setattr(workers, "broker", broker)

    async def fake_ideation_service(trend: str):
        return {"idea": f"idea-for-{trend}"}

    async def fake_image_service(data):
        return {"image": f"img-for-{data['idea']}"}

    async def fake_product_service(data):
        return {"product": f"prod-for-{data['image']}"}

    async def fake_listing_service(data):
        return {"listing": f"list-for-{data['product']}"}

    async def fake_notify(message: str) -> None:
        notifications.append(message)

    notifications: list[str] = []
    monkeypatch.setattr(workers, "call_ideation_service", fake_ideation_service)
    monkeypatch.setattr(workers, "call_image_service", fake_image_service)
    monkeypatch.setattr(workers, "call_product_service", fake_product_service)
    monkeypatch.setattr(workers, "call_listing_service", fake_listing_service)
    monkeypatch.setattr(workers, "notify", fake_notify)

    final = asyncio.Event()
    listing: dict[str, str] = {}

    async def capture(msg):
        listing.update(msg)
        final.set()

    tasks = [
        asyncio.create_task(broker.consume("trend_signals", "g1", "c1", workers.handle_trend)),
        asyncio.create_task(broker.consume("ideas_ready", "g2", "c2", workers.handle_idea)),
        asyncio.create_task(broker.consume("images_ready", "g3", "c3", workers.handle_image)),
        asyncio.create_task(broker.consume("products_ready", "g4", "c4", workers.handle_product)),
        asyncio.create_task(broker.consume("listings_ready", "g5", "c5", capture)),
    ]

    await broker.publish("trend_signals", {"trend": "cats"})
    await asyncio.wait_for(final.wait(), timeout=1)
    assert listing["listing"] == "list-for-prod-for-img-for-idea-for-cats"
    for t in tasks:
        t.cancel()
