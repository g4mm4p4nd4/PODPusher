import asyncio
import os
from datetime import timedelta
from typing import Any, Dict

import httpx
from sqlmodel import select

from .repository import aggregate_metrics, create_event, fetch_events
from ..common.database import get_session
from ..common.time import utcnow
from ..models import AnalyticsEvent, EventType, Trend, TrendSignal

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


def _normalize_keyword(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.split()).strip().lower()


async def get_trending_keywords(limit: int = 10, lookback_hours: int = 24 * 7):
    """Return top keywords from live trend signals with a Trend table fallback."""
    cutoff = utcnow() - timedelta(hours=max(1, lookback_hours))
    keyword_scores: dict[str, int] = {}

    async with get_session() as session:
        stmt = select(TrendSignal.keyword, TrendSignal.engagement_score).where(
            TrendSignal.timestamp >= cutoff
        )
        signal_rows = (await session.exec(stmt)).all()

        for keyword, score in signal_rows:
            term = _normalize_keyword(keyword)
            if not term:
                continue
            weight = max(1, int(score or 0))
            keyword_scores[term] = keyword_scores.get(term, 0) + weight

        if not keyword_scores:
            fallback_stmt = select(Trend.term).where(Trend.created_at >= cutoff)
            trend_rows = (await session.exec(fallback_stmt)).all()
            for term in trend_rows:
                normalized = _normalize_keyword(term)
                if normalized:
                    keyword_scores[normalized] = keyword_scores.get(normalized, 0) + 1

    clamped_limit = max(1, min(limit, 50))
    ranked = sorted(keyword_scores.items(), key=lambda item: (-item[1], item[0]))[
        :clamped_limit
    ]
    return [{"term": term, "clicks": clicks} for term, clicks in ranked]
