from datetime import datetime

import pytest
from sqlmodel import select

from services.common.database import get_session, init_db
from services.models import TrendSignal
from services.trend_ingestion import service
from services.trend_ingestion import scrapegraph_adapter
from services.trend_ingestion.scrapegraph_adapter import (
    PublicOnlyConfigError,
    ScrapeGraphUnavailable,
    _graph_config,
    normalize_scrapegraph_result,
    scrape_with_scrapegraph,
    validate_public_only_config,
)
from services.trend_ingestion.circuit_breaker import CircuitBreaker
from services.trend_ingestion.sources import SourceConfig, SelectorSet


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


def test_scrapegraph_adapter_normalizes_structured_trends():
    payload = {
        "trends": [
            {"keyword": "Funny Cat Shirt", "engagement_score": "1,250", "category": "animals"},
            {"term": "Funny Cat Shirt", "score": 1},
            "Minimalist Mug",
        ]
    }

    trends = normalize_scrapegraph_result("etsy", payload)

    assert trends == [
        {
            "source": "etsy",
            "keyword": "Funny Cat Shirt",
            "engagement_score": 1250,
            "category": "animals",
            "method": "scrapegraph",
            "market_examples": [
                {
                    "title": "Funny Cat Shirt",
                    "keyword": "Funny Cat Shirt",
                    "source": "etsy",
                    "source_url": None,
                    "image_url": None,
                    "engagement_score": 1250,
                    "example_type": "source_product",
                }
            ],
        },
        {
            "source": "etsy",
            "keyword": "Minimalist Mug",
            "engagement_score": 98,
            "category": "other",
            "method": "scrapegraph",
            "market_examples": [],
        },
    ]


def test_public_only_config_rejects_session_settings(monkeypatch):
    monkeypatch.setenv("TREND_INGESTION_COOKIE_FILE", "/local/cookies.json")

    with pytest.raises(PublicOnlyConfigError):
        validate_public_only_config()


def test_scrapegraph_config_maps_opencode_go_to_openai_compatible(monkeypatch):
    monkeypatch.setattr(scrapegraph_adapter, "SCRAPEGRAPH_MODEL", "opencode-go/kimi-k2.6")
    monkeypatch.setattr(scrapegraph_adapter, "SCRAPEGRAPH_API_KEY", "opencode-test-key")
    monkeypatch.setattr(scrapegraph_adapter, "OPENCODE_GO_BASE_URL", "https://opencode.ai/zen/go/v1")

    config = _graph_config()

    assert config["llm"]["model_instance"].model_name == "kimi-k2.6"
    assert str(config["llm"]["model_instance"].openai_api_base).rstrip("/") == "https://opencode.ai/zen/go/v1"
    assert config["llm"]["model_tokens"] == scrapegraph_adapter.SCRAPEGRAPH_MODEL_TOKENS


def test_scrapegraph_config_requires_opencode_go_key(monkeypatch):
    monkeypatch.setattr(scrapegraph_adapter, "SCRAPEGRAPH_MODEL", "opencode-go/deepseek-v4-flash")
    monkeypatch.setattr(scrapegraph_adapter, "SCRAPEGRAPH_API_KEY", "")

    with pytest.raises(ScrapeGraphUnavailable):
        _graph_config()


@pytest.mark.asyncio
async def test_scrapegraph_adapter_times_out_slow_public_sources(monkeypatch):
    def _slow_run(_source_name, _config):
        import time

        time.sleep(0.1)
        return {"trends": ["Funny Cat Shirt"]}

    monkeypatch.setattr(scrapegraph_adapter, "SCRAPEGRAPH_ENABLED", True)
    monkeypatch.setattr(scrapegraph_adapter, "SCRAPEGRAPH_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(scrapegraph_adapter, "_run_scrapegraph", _slow_run)

    config = SourceConfig(
        url="https://example.com/trends",
        selectors=SelectorSet(
            item=["article"],
            title=["h1"],
            hashtags=[],
            likes=[],
            shares=[],
            comments=[],
        ),
        wait_for_selector="article",
    )

    with pytest.raises(ScrapeGraphUnavailable, match="timed out"):
        await scrape_with_scrapegraph("example", config)


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
                "market_examples": [
                    {
                        "title": "Funny Cat Mug Bestseller",
                        "keyword": "funny cat mug",
                        "source": "rss",
                        "source_url": "https://example.com/funny-cat-mug",
                        "image_url": "https://example.com/funny-cat-mug.jpg",
                        "engagement_score": 42,
                        "example_type": "source_trend",
                    }
                ],
            }
        ], {
            "mode": "live",
            "sources_succeeded": ["rss"],
            "sources_failed": {},
            "source_methods": {"rss": "rss_fallback"},
            "source_diagnostics": {
                "rss": {
                    "status": "success",
                    "method": "rss_fallback",
                    "collected": 1,
                    "persisted": 0,
                }
            },
        }

    monkeypatch.setattr(service, "_gather_trends", fake_gather)

    result = await service.refresh_trends()

    assert result["last_mode"] == "live"
    assert result["signals_collected"] == 1
    assert result["signals_persisted"] == 1
    assert result["source_diagnostics"]["rss"]["persisted"] == 1
    assert result["last_finished_at"] is not None
    assert result["failed_count"] == 0

    async with get_session() as session:
        rows = (await session.exec(select(TrendSignal))).all()
    assert len(rows) == 1
    assert rows[0].keyword == "funny cat mug"
    assert rows[0].metadata_json
    assert rows[0].metadata_json["market_examples"][0]["title"] == "Funny Cat Mug Bestseller"


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
    monkeypatch.setattr(service, "RSS_FALLBACK_ENABLED", True)
    monkeypatch.setattr(service, "ALLOW_STUB_FALLBACK", True)
    monkeypatch.setattr(service, "scraper_circuit_breaker", CircuitBreaker())
    monkeypatch.setattr(service, "PLATFORM_CONFIG", {"tiktok": object()})
    monkeypatch.setattr(service, "async_playwright", lambda: _BrokenPlaywrightCtx())
    monkeypatch.setattr(service, "_fetch_rss_signals", _fake_rss)

    signals, metadata = await service._gather_trends()

    assert metadata["mode"] == "fallback_stub"
    assert metadata["sources_failed"]["playwright"] == "playwright unavailable"
    assert metadata["source_diagnostics"]["playwright"]["status"] == "failed"
    assert signals


@pytest.mark.asyncio
async def test_gather_trends_can_disable_rss_and_stub_fallback(monkeypatch):
    class _BrokenPlaywrightCtx:
        async def __aenter__(self):
            raise RuntimeError("playwright unavailable")

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(service, "STUB_ONLY", False)
    monkeypatch.setattr(service, "RSS_FALLBACK_ENABLED", False)
    monkeypatch.setattr(service, "ALLOW_STUB_FALLBACK", False)
    monkeypatch.setattr(service, "scraper_circuit_breaker", CircuitBreaker())
    monkeypatch.setattr(service, "PLATFORM_CONFIG", {"tiktok": object()})
    monkeypatch.setattr(service, "async_playwright", lambda: _BrokenPlaywrightCtx())

    signals, metadata = await service._gather_trends()

    assert signals == []
    assert metadata["mode"] == "live_empty"
    assert metadata["source_methods"]["google_trends_rss"] == "skipped"
    assert metadata["source_diagnostics"]["google_trends_rss"]["reason"] == "RSS fallback disabled"
    assert metadata["skipped_count"] == 1


@pytest.mark.asyncio
async def test_gather_trends_uses_scrapegraph_before_selector(monkeypatch):
    class _DummyPlaywrightCtx:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def _fake_scrapegraph(name, _config):
        return [
            {
                "source": name,
                "keyword": "public trend",
                "engagement_score": 77,
                "category": "other",
                "method": "scrapegraph",
            }
        ]

    async def _selector_should_not_run(*_args, **_kwargs):
        raise AssertionError("selector fallback should not run after ScrapeGraphAI success")

    async def _fake_rss():
        return []

    config = SourceConfig(
        url="https://example.com/trends",
        selectors=SelectorSet(
            item=["article"],
            title=["h1"],
            hashtags=["a"],
            likes=["span"],
            shares=["span"],
            comments=["span"],
        ),
        wait_for_selector="article",
    )

    monkeypatch.setattr(service, "STUB_ONLY", False)
    monkeypatch.setattr(service, "RSS_FALLBACK_ENABLED", True)
    monkeypatch.setattr(service, "ALLOW_STUB_FALLBACK", True)
    monkeypatch.setattr(service, "PLATFORM_CONFIG", {"public": config})
    monkeypatch.setattr(service, "async_playwright", lambda: _DummyPlaywrightCtx())
    monkeypatch.setattr(service, "scrape_with_scrapegraph", _fake_scrapegraph)
    monkeypatch.setattr(service, "_scrape_source", _selector_should_not_run)
    monkeypatch.setattr(service, "_fetch_rss_signals", _fake_rss)

    signals, metadata = await service._gather_trends()

    assert signals[0]["keyword"] == "public trend"
    assert metadata["source_methods"]["public"] == "scrapegraph"
    assert metadata["source_diagnostics"]["public"]["collected"] == 1
    assert metadata["source_methods"]["google_trends_rss"] == "failed"
    assert metadata["fallback_count"] == 0


@pytest.mark.asyncio
async def test_gather_trends_falls_back_from_scrapegraph_to_selector(monkeypatch):
    class _DummyPlaywrightCtx:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def _fake_scrapegraph(_name, _config):
        raise RuntimeError("local model unavailable")

    async def _fake_selector(_pw, name, _config):
        return [
            {
                "source": name,
                "keyword": "selector trend",
                "engagement_score": 44,
                "category": "other",
            }
        ]

    async def _fake_rss():
        return []

    config = SourceConfig(
        url="https://example.com/trends",
        selectors=SelectorSet(
            item=["article"],
            title=["h1"],
            hashtags=["a"],
            likes=["span"],
            shares=["span"],
            comments=["span"],
        ),
        wait_for_selector="article",
    )

    monkeypatch.setattr(service, "STUB_ONLY", False)
    monkeypatch.setattr(service, "RSS_FALLBACK_ENABLED", True)
    monkeypatch.setattr(service, "ALLOW_STUB_FALLBACK", True)
    monkeypatch.setattr(service, "PLATFORM_CONFIG", {"public": config})
    monkeypatch.setattr(service, "async_playwright", lambda: _DummyPlaywrightCtx())
    monkeypatch.setattr(service, "scrape_with_scrapegraph", _fake_scrapegraph)
    monkeypatch.setattr(service, "_scrape_source", _fake_selector)
    monkeypatch.setattr(service, "_fetch_rss_signals", _fake_rss)

    signals, metadata = await service._gather_trends()

    assert signals[0]["keyword"] == "selector trend"
    assert signals[0]["method"] == "selector_fallback"
    assert metadata["source_methods"]["public"] == "selector_fallback"
    assert metadata["source_diagnostics"]["public"]["fallback_from"] == "scrapegraph"
    assert metadata["source_methods"]["google_trends_rss"] == "failed"
    assert metadata["fallback_count"] == 1
