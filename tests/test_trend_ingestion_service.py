from datetime import datetime

import pytest
from sqlmodel import select

from services.common.database import get_session, init_db
from services.models import TrendSignal
from services.trend_ingestion import service
from services.trend_ingestion.circuit_breaker import CircuitBreaker


def test_extract_rss_signals_parses_items():
    xml = """
    <rss><channel>
      <item><title>Funny Cat Shirt</title></item>
      <item><title>Climate Action Poster</title></item>
    </channel></rss>
    """
    signals = service._extract_rss_signals(xml)
    assert len(signals) == 2
    assert signals[0]["source"] == "google_trends_rss"
    assert signals[0]["keyword"] == "funny cat shirt"


@pytest.mark.asyncio
async def test_refresh_trends_persists_and_updates_status(monkeypatch):
    await init_db()

    async def fake_gather():
        return [
            {
                "source": "rss",
                "keyword": "funny cat mug",
                "engagement_score": 42,
                "category": "animals",
            }
        ], {
            "mode": "live",
            "sources_succeeded": ["rss"],
            "sources_failed": {},
        }

    monkeypatch.setattr(service, "_gather_trends", fake_gather)

    result = await service.refresh_trends()

    assert result["last_mode"] == "live"
    assert result["signals_collected"] == 1
    assert result["signals_persisted"] == 1
    assert result["last_finished_at"] is not None

    async with get_session() as session:
        rows = (await session.exec(select(TrendSignal))).all()
    assert len(rows) == 1
    assert rows[0].keyword == "funny cat mug"


def test_get_refresh_status_formats_timestamps(monkeypatch):
    monkeypatch.setitem(service._refresh_status, "last_started_at", datetime(2026, 3, 6, 10, 0, 0))
    monkeypatch.setitem(service._refresh_status, "last_finished_at", datetime(2026, 3, 6, 10, 0, 1))
    monkeypatch.setitem(service._refresh_status, "last_mode", "live")
    monkeypatch.setitem(service._refresh_status, "signals_collected", 3)
    monkeypatch.setitem(service._refresh_status, "signals_persisted", 2)

    payload = service.get_refresh_status()

    assert payload["last_started_at"].startswith("2026-03-06T10:00:00")
    assert payload["last_finished_at"].startswith("2026-03-06T10:00:01")
    assert payload["last_mode"] == "live"
    assert payload["signals_collected"] == 3
    assert payload["signals_persisted"] == 2


@pytest.mark.asyncio
async def test_gather_trends_falls_back_when_playwright_boot_fails(monkeypatch):
    class _BrokenPlaywrightCtx:
        async def __aenter__(self):
            raise RuntimeError("playwright unavailable")

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def _fake_rss():
        return []

    monkeypatch.setattr(service, "STUB_ONLY", False)
    monkeypatch.setattr(service, "scraper_circuit_breaker", CircuitBreaker())
    monkeypatch.setattr(service, "PLATFORM_CONFIG", {"tiktok": object()})
    monkeypatch.setattr(service, "async_playwright", lambda: _BrokenPlaywrightCtx())
    monkeypatch.setattr(service, "_fetch_rss_signals", _fake_rss)

    signals, metadata = await service._gather_trends()

    assert metadata["mode"] == "fallback_stub"
    assert metadata["sources_failed"]["playwright"] == "playwright unavailable"
    assert signals
