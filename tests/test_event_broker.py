from __future__ import annotations

import asyncio
from contextlib import suppress

import pytest
from redis.exceptions import ResponseError

from packages.broker.broker import EventBroker


class FakeRedis:
    def __init__(self) -> None:
        self._streams: dict[str, list[tuple[str, dict[str, str]]]] = {}
        self._groups: set[tuple[str, str]] = set()
        self._acked: list[tuple[str, str, str]] = []
        self._sequence = 0

    async def xgroup_create(self, stream: str, group: str, id: str = "0", mkstream: bool = True) -> None:
        key = (stream, group)
        if key in self._groups:
            raise ResponseError("BUSYGROUP Consumer Group name already exists")
        self._groups.add(key)
        if mkstream:
            self._streams.setdefault(stream, [])

    async def xadd(self, stream: str, payload: dict[str, str]) -> str:
        self._sequence += 1
        message_id = f"{self._sequence}-0"
        self._streams.setdefault(stream, []).append((message_id, payload))
        return message_id

    async def xreadgroup(
        self,
        group: str,
        consumer: str,
        streams: dict[str, str],
        count: int = 1,
        block: int = 1000,
    ):
        del consumer, block
        for stream in streams:
            if (stream, group) not in self._groups:
                raise ResponseError("NOGROUP No such consumer group")
            messages = self._streams.get(stream, [])
            if messages:
                message = messages.pop(0)
                return [(stream, [message])]
        return []

    async def xack(self, stream: str, group: str, message_id: str) -> int:
        self._acked.append((stream, group, message_id))
        return 1

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_publish_and_consume_round_trips_json_payload() -> None:
    redis = FakeRedis()
    broker = EventBroker(redis=redis, block_ms=10)
    received: dict[str, object] = {}
    delivered = asyncio.Event()

    async def handler(message: dict[str, object]) -> None:
        received.update(message)
        delivered.set()

    task = asyncio.create_task(broker.consume("trend_signals", "g1", "c1", handler))
    await broker.publish(
        "trend_signals",
        {"user_id": 7, "trend": "cats", "source": "manual", "auto": False},
    )

    await asyncio.wait_for(delivered.wait(), timeout=1)
    assert received == {
        "user_id": 7,
        "trend": "cats",
        "source": "manual",
        "auto": False,
    }

    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
    await broker.close()


@pytest.mark.asyncio
async def test_broker_constructs_client_without_await(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, bool]] = []

    class DummyRedis:
        async def close(self) -> None:
            return None

    dummy = DummyRedis()

    def fake_from_url(url: str | None, *, decode_responses: bool = False):
        calls.append((url or "", decode_responses))
        return dummy

    monkeypatch.setattr("packages.broker.broker.from_url", fake_from_url)

    broker = EventBroker(url="redis://example:6379/0")
    conn = await broker._conn()

    assert conn is dummy
    assert calls == [("redis://example:6379/0", True)]
    await broker.close()
