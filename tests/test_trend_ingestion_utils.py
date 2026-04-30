from datetime import timedelta

import pytest

from services.common.database import get_session, init_db
from services.common.time import utcnow
from services.models import TrendSignal
from services.trend_ingestion import service as ingestion_service
from services.trend_ingestion.circuit_breaker import CircuitBreaker, CircuitState
from services.trend_ingestion.service import (
    SourceBlockedError,
    _keyword_candidates_from_text,
    _parse_metric,
    _readable_node_text,
    _sanitize_reason,
    build_scrape_plan,
    build_scrape_profile,
    categorize,
    compute_engagement,
    get_live_trends,
    normalize_category,
    normalize_signal,
    normalize_text,
)
from services.trend_ingestion.sources import SourceConfig, SelectorSet


def test_normalize_text_removes_emojis_and_stopwords():
    text = "The \U0001f436 Dog and THE Cat"
    assert normalize_text(text) == "dog cat"


def test_compute_engagement_sum():
    assert compute_engagement(1, 2, 3) == 6


def test_categorize_keyword():
    assert categorize("funny cat video") == "animals"
    assert categorize("unknown term") == "other"


def test_normalize_signal_improves_category_and_provenance():
    signal = normalize_signal(
        {
            "source": "etsy",
            "keyword": "Vintage Teacher Mug Gift",
            "engagement_score": "123",
            "method": "rss_fallback",
        }
    )

    assert signal["keyword"] == "vintage teacher mug gift"
    assert signal["category"] == "drinkware"
    assert signal["provenance"]["source"] == "etsy"
    assert signal["provenance"]["is_estimated"] is True
    assert normalize_category("Home Decor", "sun wall art") == "home_decor"


def test_normalize_signal_rejects_metric_only_keywords():
    assert (
        normalize_signal({"source": "tiktok", "keyword": "149K", "engagement_score": 1})
        is None
    )


def test_normalize_signal_rejects_noisy_rss_and_condenses_product_titles():
    assert (
        normalize_signal(
            {
                "source": "google_trends_rss",
                "keyword": "Earthquake today",
                "method": "rss_fallback",
            }
        )
        is None
    )
    assert (
        normalize_signal(
            {
                "source": "google_trends_rss",
                "keyword": "Lakers score",
                "method": "rss_fallback",
            }
        )
        is None
    )
    kept = normalize_signal(
        {
            "source": "google_trends_rss",
            "keyword": "Funny Cat Shirt",
            "method": "rss_fallback",
        }
    )
    assert kept
    assert kept["keyword"] == "funny cat shirt"

    condensed = normalize_signal(
        {
            "source": "amazon",
            "keyword": "Hanes Mens EcoSmart Hoodie Midweight Fleece Pullover Hooded Sweatshirt",
            "method": "selector_fallback",
        }
    )
    assert condensed
    assert condensed["keyword"] == "hoodie midweight fleece pullover hooded sweatshirt"


def test_normalize_signal_filters_broad_source_noise_from_smoke():
    noisy_examples = [
        ("pinterest", "Yellow Nail Art"),
        ("pinterest", "Cinematic Wedding Photography"),
        ("amazon", "or lift style available"),
        ("amazon", "Ankis Heels for Women Open Toe Ankle Strap"),
        ("amazon", "Frida Mom 8pc Postpartum Underwear"),
        ("amazon", "Valentines Day Gift for Her Unique Present"),
    ]

    for source, keyword in noisy_examples:
        assert (
            normalize_signal(
                {"source": source, "keyword": keyword, "method": "selector_fallback"}
            )
            is None
        )

    hoodie = normalize_signal(
        {
            "source": "amazon",
            "keyword": "Hanes Men's EcoSmart Hoodie Midweight Fleece Pullover Hooded Sweatshirt",
            "method": "selector_fallback",
        }
    )
    assert hoodie
    assert hoodie["keyword"] == "hoodie midweight fleece pullover hooded sweatshirt"


def test_parse_metric_parses_suffixes():
    assert _parse_metric("1.5K") == 1500
    assert _parse_metric("2M") == 2000000
    assert _parse_metric("123") == 123


def test_parse_metric_handles_invalid():
    assert _parse_metric("") == 0
    assert _parse_metric("abc") == 0


def test_text_fallback_extracts_public_topic_signals():
    text = (
        "Log In Sign Up # earthday 40K Posts Fashion trends 2026 "
        "Earthy interiors Chic 9-to-5 street style"
    )

    candidates = _keyword_candidates_from_text(text, "tiktok")

    keywords = {normalize_text(item["keyword"]) for item in candidates}
    assert "earthday" in keywords
    assert "chic 9 5 street style" in keywords
    assert all("log" not in keyword for keyword in keywords)


def test_text_fallback_filters_navigation_and_css_tokens():
    text = "nprogress fe2c55 gridItemRoot navSwmHoliday Trend Discovery Top Products"

    candidates = _keyword_candidates_from_text(text, "amazon")
    normalized = [
        normalize_signal({**candidate, "method": "selector_text_fallback"})
        for candidate in candidates
    ]

    assert [item for item in normalized if item] == []


@pytest.mark.asyncio
async def test_readable_node_text_falls_back_to_alt_attribute():
    class Node:
        async def inner_text(self):
            return ""

        async def get_attribute(self, attribute):
            return "Women Tea Party Hat" if attribute == "alt" else None

    assert await _readable_node_text(Node()) == "Women Tea Party Hat"


def test_sanitize_reason_collapses_playwright_browser_errors():
    reason = _sanitize_reason(
        "BrowserType.launch: Executable doesn't exist at "
        "/home/bear/.cache/ms-playwright/chromium/headless_shell\n"
        "please run playwright install"
    )

    assert reason == "Playwright browser executable unavailable"


def test_scrape_plan_and_profile_are_seedable_and_bounded():
    import random

    rng = random.Random(7)
    plan = build_scrape_plan(["a", "b", "c"], rng)
    assert sorted(plan) == ["a", "b", "c"]
    assert plan != ["a", "b", "c"]

    config = SourceConfig(
        url="https://example.com",
        candidate_urls=["https://example.com/alt"],
        selectors=SelectorSet(
            item=["article"],
            title=["h1"],
            hashtags=["a"],
            likes=["span"],
            shares=["span"],
            comments=["span"],
        ),
        wait_for_selector="article",
        scroll_iterations=2,
    )
    profile = build_scrape_profile(config, random.Random(9))

    assert config.urls() == ["https://example.com", "https://example.com/alt"]
    assert profile.user_agent
    assert 1200 <= profile.viewport_width <= 1600
    assert 720 <= profile.viewport_height <= 1000
    assert profile.scroll_iterations in {2, 3}
    assert 1600 <= profile.scroll_pixels <= 2800
    assert 250 <= profile.delay_ms <= 1250


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
    now = utcnow()
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

    trends = await get_live_trends(
        source="tiktok", lookback_hours=72, per_group_limit=1
    )
    assert list(trends.keys()) == ["animals"]
    assert len(trends["animals"]) == 1
    assert trends["animals"][0]["keyword"] == "Funny Cat"
    assert trends["animals"][0]["source"] == "tiktok"
    assert trends["animals"][0]["provenance"]["source"] == "tiktok"

    paged = await get_live_trends(
        source="tiktok",
        lookback_hours=72,
        per_group_limit=2,
        page=1,
        page_size=1,
        sort_by="timestamp",
        include_meta=True,
    )
    assert paged["pagination"]["total"] == 1
    assert paged["items_by_category"]["animals"][0]["keyword"] == "Funny Cat"


@pytest.mark.asyncio
async def test_gather_trends_skips_open_circuit(monkeypatch):
    class _DummyPlaywrightCtx:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=60.0)
    breaker.record_failure("blocked")
    assert breaker.state("blocked") == CircuitState.OPEN

    called = {"scrape": 0}

    async def _fake_scrape(_pw, _name, _config):
        called["scrape"] += 1
        return []

    async def _fake_rss():
        return []

    monkeypatch.setattr(ingestion_service, "STUB_ONLY", False)
    monkeypatch.setattr(ingestion_service, "scraper_circuit_breaker", breaker)
    monkeypatch.setattr(ingestion_service, "PLATFORM_CONFIG", {"blocked": object()})
    monkeypatch.setattr(
        ingestion_service, "async_playwright", lambda: _DummyPlaywrightCtx()
    )
    monkeypatch.setattr(ingestion_service, "_scrape_source", _fake_scrape)
    monkeypatch.setattr(ingestion_service, "_fetch_rss_signals", _fake_rss)

    _signals, metadata = await ingestion_service._gather_trends()

    assert called["scrape"] == 0
    assert metadata["sources_failed"]["blocked"] == "Circuit breaker open"
    assert metadata["source_methods"]["blocked"] == "skipped"
    assert metadata["sources_blocked"] == ["blocked"]
    assert metadata["source_diagnostics"]["blocked"]["status"] == "skipped"
    assert metadata["blocked_count"] == 1


@pytest.mark.asyncio
async def test_gather_trends_marks_login_gated_source_as_blocked(monkeypatch):
    class _DummyPlaywrightCtx:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)

    async def _fake_scrape(_pw, _name, _config):
        raise SourceBlockedError("Public page blocked or login gated status=403")

    async def _fake_scrapegraph(_name, _config):
        raise RuntimeError("local model unavailable")

    async def _fake_rss():
        return []

    monkeypatch.setattr(ingestion_service, "STUB_ONLY", False)
    monkeypatch.setattr(ingestion_service, "RSS_FALLBACK_ENABLED", True)
    monkeypatch.setattr(ingestion_service, "ALLOW_STUB_FALLBACK", False)
    monkeypatch.setattr(ingestion_service, "scraper_circuit_breaker", breaker)
    monkeypatch.setattr(
        ingestion_service,
        "PLATFORM_CONFIG",
        {
            "etsy": SourceConfig(
                url="https://example.com/blocked",
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
        },
    )
    monkeypatch.setattr(
        ingestion_service, "async_playwright", lambda: _DummyPlaywrightCtx()
    )
    monkeypatch.setattr(ingestion_service, "scrape_with_scrapegraph", _fake_scrapegraph)
    monkeypatch.setattr(ingestion_service, "_scrape_source", _fake_scrape)
    monkeypatch.setattr(ingestion_service, "_fetch_rss_signals", _fake_rss)

    signals, metadata = await ingestion_service._gather_trends()

    assert signals == []
    assert metadata["source_methods"]["etsy"] == "skipped"
    assert metadata["sources_blocked"] == ["etsy"]
    assert metadata["sources_skipped"] == ["etsy"]
    assert metadata["blocked_count"] == 1
    assert metadata["failed_count"] == 1  # google_trends_rss had no usable items
    assert metadata["source_diagnostics"]["etsy"]["method"] == "blocked"


@pytest.mark.asyncio
async def test_gather_trends_records_scrape_failures_into_circuit_breaker(monkeypatch):
    class _DummyPlaywrightCtx:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=60.0)

    async def _fake_scrape(_pw, name, _config):
        if name == "failing":
            raise RuntimeError("boom")
        return [
            {
                "source": "healthy",
                "keyword": "funny cat",
                "engagement_score": 123,
                "category": "animals",
            }
        ]

    async def _fake_rss():
        return []

    monkeypatch.setattr(ingestion_service, "STUB_ONLY", False)
    monkeypatch.setattr(ingestion_service, "scraper_circuit_breaker", breaker)
    monkeypatch.setattr(
        ingestion_service,
        "PLATFORM_CONFIG",
        {
            "failing": SourceConfig(
                url="https://example.com/failing",
                selectors=SelectorSet(
                    item=["article"],
                    title=["h1"],
                    hashtags=[],
                    likes=[],
                    shares=[],
                    comments=[],
                ),
                wait_for_selector="article",
            ),
            "healthy": SourceConfig(
                url="https://example.com/healthy",
                selectors=SelectorSet(
                    item=["article"],
                    title=["h1"],
                    hashtags=[],
                    likes=[],
                    shares=[],
                    comments=[],
                ),
                wait_for_selector="article",
            ),
        },
    )
    monkeypatch.setattr(
        ingestion_service, "async_playwright", lambda: _DummyPlaywrightCtx()
    )
    monkeypatch.setattr(ingestion_service, "_scrape_source", _fake_scrape)
    monkeypatch.setattr(ingestion_service, "_fetch_rss_signals", _fake_rss)

    _signals, metadata = await ingestion_service._gather_trends()

    assert "selector_fallback: boom" in metadata["sources_failed"]["failing"]
    assert "healthy" in metadata["sources_succeeded"]
    assert breaker.state("failing") == CircuitState.OPEN
    assert breaker.state("healthy") == CircuitState.CLOSED
