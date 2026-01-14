import asyncio
import os
import httpx
from typing import Dict, Any
from .repository import create_event, fetch_events, aggregate_metrics
from ..common.database import get_session
from ..models import AnalyticsEvent, EventType

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
    event_type: EventType,
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
    if event_type == EventType.conversion:
        quantity = 1
        if meta and isinstance(meta, dict):
            raw = meta.get("quantity") or meta.get("value")
            try:
                quantity = max(1, int(raw))
            except (TypeError, ValueError):
                quantity = 1
        asyncio.create_task(_report_conversion_to_stripe(quantity))
    return created


async def list_events(event_type: EventType | None = None):
    async with get_session() as session:
        return await fetch_events(session, event_type)


async def get_summary():
    async with get_session() as session:
        rows = await aggregate_metrics(session)
    summary = []
    for path, views, clicks, conversions in rows:
        rate = (conversions / views) if views else 0
        summary.append(
            {
                "path": path,
                "views": views,
                "clicks": clicks,
                "conversions": conversions,
                "conversion_rate": rate,
            }
        )
    return summary
