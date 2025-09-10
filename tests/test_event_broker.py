import asyncio

import fakeredis.aioredis
import pytest

from packages.broker import EventBroker


@pytest.mark.asyncio
async def test_publish_and_consume() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    broker = EventBroker(redis=redis)
    received: dict[str, str] = {}
    event = asyncio.Event()

    async def handler(msg: dict[str, str]) -> None:
        received.update(msg)
        event.set()

    task = asyncio.create_task(broker.consume("test_stream", "group", "c1", handler))
    await broker.publish("test_stream", {"foo": "bar"})
    await asyncio.wait_for(event.wait(), timeout=1)
    assert received["foo"] == "bar"
    task.cancel()
