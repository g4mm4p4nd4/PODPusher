from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable

from redis.asyncio import Redis, from_url
from redis.exceptions import ResponseError


MessageHandler = Callable[[dict[str, Any]], Awaitable[None]]


def _encode_message(message: dict[str, Any]) -> dict[str, str]:
    return {key: json.dumps(value) for key, value in message.items()}


def _decode_message(message: dict[str, str]) -> dict[str, Any]:
    decoded: dict[str, Any] = {}
    for key, value in message.items():
        try:
            decoded[key] = json.loads(value)
        except json.JSONDecodeError:
            decoded[key] = value
    return decoded


class EventBroker:
    """Minimal Redis Streams publisher/consumer with JSON payload support."""

    def __init__(
        self,
        url: str | None = None,
        redis: Redis | None = None,
        *,
        block_ms: int = 1000,
    ) -> None:
        if not url and redis is None:
            raise ValueError("url or redis instance required")
        self._url = url
        self._redis = redis
        self._block_ms = block_ms

    async def _conn(self) -> Redis:
        if self._redis is None:
            # redis.asyncio.from_url is synchronous and returns a client instance.
            self._redis = from_url(self._url, decode_responses=True)
        return self._redis

    async def publish(self, stream: str, message: dict[str, Any]) -> str:
        redis = await self._conn()
        return await redis.xadd(stream, _encode_message(message))

    async def consume(
        self,
        stream: str,
        group: str,
        consumer: str,
        handler: MessageHandler,
    ) -> None:
        redis = await self._conn()
        try:
            await redis.xgroup_create(stream, group, id="0", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

        while True:
            entries = await redis.xreadgroup(
                group,
                consumer,
                {stream: ">"},
                count=1,
                block=self._block_ms,
            )
            if not entries:
                await asyncio.sleep(0)
                continue

            for _stream_name, messages in entries:
                for message_id, payload in messages:
                    await handler(_decode_message(payload))
                    await redis.xack(stream, group, message_id)

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
