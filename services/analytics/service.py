import asyncio
import os
import httpx
import asyncio
import os
from typing import Dict, Any

import httpx

from .repository import (
    create_event,
    fetch_events,
    aggregate_events,
    create_metric,
    fetch_metrics,
)
from ..common.database import get_session
from ..models import AnalyticsEvent, Metric
from .exporter import export_event

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")


async def _report_conversion_to_stripe(quantity: int = 1) -> None:
    if not STRIPE_API_KEY:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                "https://api.stripe.com/v1/usage_records",
                auth=(STRIPE_API_KEY, ""),
                data={"quantity": quantity},
            )
    except httpx.HTTPError as exc:
        # log but do not raise to keep latency low
        print(f"Stripe usage report failed: {exc}")


async def log_event(
    event_type: str,
    path: str,
    user_id: int | None = None,
    meta: Dict[str, Any] | None = None,
) -> AnalyticsEvent:
    async with get_session() as session:
        event = AnalyticsEvent(
            event_type=event_type,
            path=path,
            user_id=user_id,
            meta=meta,
        )
        created = await create_event(session, event)
    if event_type == "conversion":
        asyncio.create_task(_report_conversion_to_stripe())
    asyncio.create_task(export_event(created))
    return created


async def list_events(event_type: str | None = None):
    async with get_session() as session:
        return await fetch_events(session, event_type)


async def get_summary(event_type: str | None = None):
    async with get_session() as session:
        rows = await aggregate_events(session, event_type)
    return [
        {"path": path, "count": count} for path, count in rows
    ]


async def create_metric_entry(name: str, value: float) -> Metric:
    async with get_session() as session:
        metric = Metric(name=name, value=value)
        return await create_metric(session, metric)


async def list_metrics() -> list[Metric]:
    async with get_session() as session:
        return await fetch_metrics(session)
