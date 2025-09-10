import asyncio
from typing import Any, Callable, Dict, Awaitable

from redis.asyncio import Redis, from_url
from redis.exceptions import ResponseError


class EventBroker:
    """Minimal Redis Streams publisher/consumer."""

    def __init__(self, url: str | None = None, redis: Redis | None = None) -> None:
        if not url and not redis:
            raise ValueError("url or redis instance required")
        self._url = url
        self._redis: Redis | None = redis

    async def _conn(self) -> Redis:
        if self._redis is None:
            self._redis = await from_url(self._url, decode_responses=True)
        return self._redis

    async def publish(self, stream: str, message: Dict[str, Any]) -> None:
        redis = await self._conn()
        await redis.xadd(stream, message)

    async def consume(
        self,
        stream: str,
        group: str,
        consumer: str,
        handler: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        redis = await self._conn()
        try:
            await redis.xgroup_create(stream, group, id="0", mkstream=True)
        except ResponseError as exc:  # group may already exist
            if "BUSYGROUP" not in str(exc):
                raise
        while True:
            entries = await redis.xreadgroup(group, consumer, {stream: ">"}, count=1, block=1000)
            if not entries:
                await asyncio.sleep(0.1)
                continue
            for _stream, messages in entries:
                for msg_id, msg in messages:
                    await handler(msg)
                    await redis.xack(stream, group, msg_id)

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
