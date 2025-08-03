import os

import httpx
from aiolimiter import AsyncLimiter

from ..models import AnalyticsEvent

EXTERNAL_ANALYTICS_URL = os.getenv("EXTERNAL_ANALYTICS_URL")
_limiter = AsyncLimiter(10, 1)  # 10 requests per second


async def export_event(event: AnalyticsEvent) -> None:
    """Export a single event to an external analytics endpoint.

    Uses a shared rate limiter and swallows network errors so that
    exporting never blocks the main application flow.
    """

    if not EXTERNAL_ANALYTICS_URL:
        return
    async with _limiter:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(
                    EXTERNAL_ANALYTICS_URL,
                    json=event.model_dump(),
                )
        except httpx.HTTPError as exc:
            # Log and swallow errors per IN-05
            print(f"export failed: {exc}")
