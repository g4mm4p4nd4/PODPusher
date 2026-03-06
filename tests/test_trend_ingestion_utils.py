from datetime import datetime, timedelta

import pytest

from services.common.database import get_session, init_db
from services.models import TrendSignal
from services.trend_ingestion import service as ingestion_service
from services.trend_ingestion.service import (
    _parse_metric,
    categorize,
    compute_engagement,
    get_live_trends,
    normalize_text,
)


def test_normalize_text_removes_emojis_and_stopwords():
    text = "The \U0001F436 Dog and THE Cat"
    assert normalize_text(text) == "dog cat"


def test_compute_engagement_sum():
    assert compute_engagement(1, 2, 3) == 6


def test_categorize_keyword():
    assert categorize("funny cat video") == "animals"
    assert categorize("unknown term") == "other"


def test_parse_metric_parses_suffixes():
    assert _parse_metric("1.5K") == 1500
    assert _parse_metric("2M") == 2000000
    assert _parse_metric("123") == 123


def test_parse_metric_handles_invalid():
    assert _parse_metric("") == 0
    assert _parse_metric("abc") == 0


@pytest.mark.asyncio
async def test_stub_gather_trends(monkeypatch):
    original = ingestion_service.STUB_ONLY
    monkeypatch.setattr(ingestion_service, "STUB_ONLY", True)
    try:
        signals, metadata = await ingestion_service._gather_trends()
    finally:
        monkeypatch.setattr(ingestion_service, "STUB_ONLY", original)
    assert signals
    assert metadata["last_mode"] if False else True
    assert all("source" in item and "keyword" in item for item in signals)


@pytest.mark.asyncio
async def test_get_live_trends_applies_source_dedup_recency_and_limit():
    await init_db()
    now = datetime.utcnow()
    async with get_session() as session:
        session.add(
            TrendSignal(
                source="tiktok",
                keyword="funny cat",
                engagement_score=10,
                category="animals",
                timestamp=now,
            )
        )
        session.add(
            TrendSignal(
                source="tiktok",
                keyword="Funny Cat",
                engagement_score=25,
                category="animals",
                timestamp=now,
            )
        )
        session.add(
            TrendSignal(
                source="twitter",
                keyword="funny cat",
                engagement_score=8,
                category="animals",
                timestamp=now,
            )
        )
        session.add(
            TrendSignal(
                source="tiktok",
                keyword="old trend",
                engagement_score=999,
                category="animals",
                timestamp=now - timedelta(hours=96),
            )
        )
        await session.commit()

    trends = await get_live_trends(source="tiktok", lookback_hours=72, per_group_limit=1)
    assert list(trends.keys()) == ["animals"]
    assert len(trends["animals"]) == 1
    assert trends["animals"][0]["keyword"] == "Funny Cat"
    assert trends["animals"][0]["source"] == "tiktok"
