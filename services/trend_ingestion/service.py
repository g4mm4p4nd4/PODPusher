import asyncio
import logging
import os
import random
import re
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Sequence
from uuid import uuid4

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from playwright.async_api import async_playwright
from sqlmodel import select

from ..common.database import get_session
from ..common.observability import Counter, Histogram
from ..models import TrendSignal
from .circuit_breaker import scraper_circuit_breaker
from .scrapegraph_adapter import (
    PublicOnlyConfigError,
    scrape_with_scrapegraph,
    validate_public_only_config,
)
from .sources import PLATFORM_CONFIG, SourceConfig, SelectorSet

logger = logging.getLogger(__name__)

SCRAPE_TOTAL = Counter(
    "pod_scrape_total",
    "Total scrape attempts by platform and outcome",
    labelnames=("platform", "outcome"),
)
SCRAPE_DURATION = Histogram(
    "pod_scrape_duration_seconds",
    "Duration of scrape operations by platform",
    labelnames=("platform",),
)
SCRAPE_KEYWORDS = Counter(
    "pod_scrape_keywords_total",
    "Total keywords extracted per platform",
    labelnames=("platform",),
)
SCRAPE_METHOD_TOTAL = Counter(
    "pod_scrape_method_total",
    "Scrape attempts by platform, extraction method, and outcome",
    labelnames=("platform", "method", "outcome"),
)
SCRAPE_FALLBACK_TOTAL = Counter(
    "pod_scrape_fallback_total",
    "Scrape fallback transitions by platform and extraction method",
    labelnames=("platform", "from_method", "to_method"),
)
SCRAPE_PERSISTED = Counter(
    "pod_scrape_persisted_total",
    "Trend signals persisted by source",
    labelnames=("source",),
)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/118.0",
]

STOPWORDS = {"the", "and", "a", "of", "to", "in"}
EMOJI_RE = re.compile(r"[\U00010000-\U0010FFFF]", flags=re.UNICODE)

SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
PLAYWRIGHT_PROXY = os.getenv("PLAYWRIGHT_PROXY")
TOP_K = int(os.getenv("TREND_INGESTION_TOP_K", "5"))
SCRAPER_TIMEOUT_MS = int(os.getenv("TREND_INGESTION_TIMEOUT_MS", "15000"))
STUB_ONLY = os.getenv("TREND_INGESTION_STUB", "0").lower() in {"1", "true", "yes"}
TREND_RSS_URL = os.getenv("TREND_INGESTION_RSS_URL", "https://trends.google.com/trending/rss?geo=US")
DEFAULT_LOOKBACK_HOURS = int(os.getenv("TREND_INGESTION_LOOKBACK_HOURS", "72"))
MAX_LIVE_TRENDS_PER_GROUP = int(os.getenv("TREND_INGESTION_MAX_LIVE_PER_GROUP", "50"))
RANDOM_SEED = os.getenv("TREND_INGESTION_RANDOM_SEED")


@dataclass(frozen=True)
class ScrapeProfile:
    user_agent: str
    viewport_width: int
    viewport_height: int
    locale: str
    timezone_id: str
    scroll_iterations: int
    scroll_pixels: int
    delay_ms: int


scheduler = AsyncIOScheduler()

_refresh_status: Dict[str, Any] = {
    "last_started_at": None,
    "last_finished_at": None,
    "last_mode": "idle",
    "sources_succeeded": [],
    "sources_failed": {},
    "source_methods": {},
    "sources_skipped": [],
    "signals_collected": 0,
    "signals_persisted": 0,
    "failed_count": 0,
    "fallback_count": 0,
    "skipped_count": 0,
}


def normalize_text(text: str) -> str:
    """Lowercase text, remove emojis and stopwords."""
    text = EMOJI_RE.sub("", text).lower()
    words = [word for word in re.split(r"\W+", text) if word and word not in STOPWORDS]
    return " ".join(words)


def compute_engagement(likes: int, shares: int, comments: int) -> int:
    return likes + shares + comments


CATEGORIES: Dict[str, List[str]] = {
    "animals": ["cat", "dog", "pet", "animal"],
    "activism": ["protest", "climate", "justice", "rights"],
    "sports": ["game", "soccer", "basketball", "tennis"],
}


def categorize(keyword: str) -> str:
    for category, keys in CATEGORIES.items():
        if any(key in keyword for key in keys):
            return category
    return "other"


def _stub_signals() -> List[Dict[str, Any]]:
    samples = [
        ("tiktok", "funny cat dance", 4200),
        ("instagram", "minimalist home decor", 2750),
        ("twitter", "eco friendly tips", 1900),
        ("etsy", "personalised gift ideas", 1650),
    ]
    signals: List[Dict[str, Any]] = []
    for source, phrase, engagement in samples:
        keyword = normalize_text(phrase)
        signals.append(
            {
                "source": source,
                "keyword": keyword,
                "engagement_score": engagement,
                "category": categorize(keyword),
            }
        )
    return signals


def _format_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def get_refresh_status() -> Dict[str, Any]:
    return {
        "last_started_at": _format_timestamp(_refresh_status.get("last_started_at")),
        "last_finished_at": _format_timestamp(_refresh_status.get("last_finished_at")),
        "last_mode": _refresh_status.get("last_mode", "idle"),
        "sources_succeeded": list(_refresh_status.get("sources_succeeded", [])),
        "sources_failed": dict(_refresh_status.get("sources_failed", {})),
        "source_methods": dict(_refresh_status.get("source_methods", {})),
        "sources_skipped": list(_refresh_status.get("sources_skipped", [])),
        "signals_collected": int(_refresh_status.get("signals_collected", 0)),
        "signals_persisted": int(_refresh_status.get("signals_persisted", 0)),
        "failed_count": int(_refresh_status.get("failed_count", 0)),
        "fallback_count": int(_refresh_status.get("fallback_count", 0)),
        "skipped_count": int(_refresh_status.get("skipped_count", 0)),
    }


def _new_rng() -> random.Random:
    if RANDOM_SEED is None:
        return random.Random()
    try:
        seed: int | str = int(RANDOM_SEED)
    except ValueError:
        seed = RANDOM_SEED
    return random.Random(seed)


def build_scrape_plan(source_names: Sequence[str] | None = None, rng: random.Random | None = None) -> List[str]:
    names = list(source_names or PLATFORM_CONFIG.keys())
    active_rng = rng or _new_rng()
    active_rng.shuffle(names)
    return names


def build_scrape_profile(config: SourceConfig, rng: random.Random | None = None) -> ScrapeProfile:
    active_rng = rng or _new_rng()
    configured_scrolls = int(getattr(config, "scroll_iterations", 0) or 0)
    return ScrapeProfile(
        user_agent=active_rng.choice(USER_AGENTS),
        viewport_width=active_rng.randint(1200, 1600),
        viewport_height=active_rng.randint(720, 1000),
        locale=active_rng.choice(["en-US", "en-GB"]),
        timezone_id=active_rng.choice(["America/New_York", "America/Chicago", "America/Los_Angeles"]),
        scroll_iterations=max(0, configured_scrolls + active_rng.randint(0, 1)),
        scroll_pixels=active_rng.randint(1600, 2800),
        delay_ms=active_rng.randint(250, 1250),
    )


async def _first_text(handle, selectors: Sequence[str]) -> str:
    for selector in selectors:
        try:
            node = await handle.query_selector(selector)
        except Exception:
            node = None
        if node:
            try:
                text = (await node.inner_text()).strip()
            except Exception:
                text = ""
            if text:
                return text
    return ""


async def _collect_texts(handle, selectors: Sequence[str]) -> List[str]:
    values: List[str] = []
    for selector in selectors:
        try:
            nodes = await handle.query_selector_all(selector)
        except Exception:
            nodes = []
        for node in nodes:
            try:
                text = (await node.inner_text()).strip()
            except Exception:
                text = ""
            if text:
                values.append(text)
    return values


def _parse_metric(value: str) -> int:
    if not value:
        return 0
    cleaned = value.strip().lower().replace(",", "")
    match = re.findall(r"\d+(?:\.\d+)?", cleaned)
    if not match:
        return 0
    base = float(match[0])
    if "m" in cleaned:
        base *= 1_000_000
    elif "k" in cleaned:
        base *= 1_000
    return int(base)


async def _collect_items(page, selectors: SelectorSet) -> List[Any]:
    collected = []
    seen_ids: set[int] = set()
    for css in selectors.item:
        try:
            handles = await page.query_selector_all(css)
        except Exception:
            handles = []
        for handle in handles:
            ident = id(handle)
            if ident in seen_ids:
                continue
            seen_ids.add(ident)
            collected.append(handle)
    return collected


async def _scrape_source(
    playwright,
    name: str,
    config: SourceConfig,
    profile: ScrapeProfile | None = None,
) -> List[Dict[str, Any]]:
    active_profile = profile or build_scrape_profile(config)
    proxy_settings = {"server": PLAYWRIGHT_PROXY} if PLAYWRIGHT_PROXY else None
    browser = await playwright.chromium.launch(headless=True, proxy=proxy_settings)
    context = await browser.new_context(
        user_agent=active_profile.user_agent,
        viewport={
            "width": active_profile.viewport_width,
            "height": active_profile.viewport_height,
        },
        locale=active_profile.locale,
        timezone_id=active_profile.timezone_id,
    )
    page = await context.new_page()
    results: List[Dict[str, Any]] = []
    try:
        await page.wait_for_timeout(active_profile.delay_ms)
        await page.goto(config.url, wait_until="networkidle", timeout=SCRAPER_TIMEOUT_MS)
        try:
            await page.wait_for_selector(config.wait_for_selector, timeout=SCRAPER_TIMEOUT_MS)
        except Exception:
            pass
        for _ in range(active_profile.scroll_iterations):
            await page.mouse.wheel(0, active_profile.scroll_pixels)
            await page.wait_for_timeout(active_profile.delay_ms)
        items = await _collect_items(page, config.selectors)
        for handle in items[: TOP_K * 2]:
            title = await _first_text(handle, config.selectors.title)
            hashtags = await _collect_texts(handle, config.selectors.hashtags)
            likes_text = await _first_text(handle, config.selectors.likes)
            shares_text = await _first_text(handle, config.selectors.shares)
            comments_text = await _first_text(handle, config.selectors.comments)
            keyword = normalize_text(" ".join(filter(None, [title, " ".join(hashtags)])))
            if not keyword:
                continue
            engagement = compute_engagement(
                _parse_metric(likes_text),
                _parse_metric(shares_text),
                _parse_metric(comments_text),
            )
            results.append(
                {
                    "source": name,
                    "keyword": keyword,
                    "engagement_score": engagement,
                    "category": categorize(keyword),
                }
            )
    finally:
        await context.close()
        await browser.close()
    return results


async def _call_selector_scraper(
    playwright,
    name: str,
    config: SourceConfig,
    profile: ScrapeProfile,
) -> List[Dict[str, Any]]:
    try:
        return await _scrape_source(playwright, name, config, profile)
    except TypeError as exc:
        # Some tests monkeypatch _scrape_source with the older 3-argument shape.
        if "argument" not in str(exc) and "positional" not in str(exc):
            raise
        return await _scrape_source(playwright, name, config)  # type: ignore[misc]


async def _scrape_with_circuit_breaker(
    playwright,
    name: str,
    config: SourceConfig,
    profile: ScrapeProfile | None = None,
) -> List[Dict[str, Any]]:
    """Scrape a single source and record scrape metrics."""
    active_profile = profile or build_scrape_profile(config)
    started = time.monotonic()
    try:
        results = await _call_selector_scraper(playwright, name, config, active_profile)
    except Exception as exc:
        duration = time.monotonic() - started
        SCRAPE_DURATION.labels(name).observe(duration)
        SCRAPE_TOTAL.labels(name, "failure").inc()
        SCRAPE_METHOD_TOTAL.labels(name, "selector_fallback", "failure").inc()
        logger.error("Scrape failed for %s after %.1fs: %s", name, duration, exc)
        raise

    duration = time.monotonic() - started
    SCRAPE_DURATION.labels(name).observe(duration)
    if results:
        SCRAPE_TOTAL.labels(name, "success").inc()
        SCRAPE_METHOD_TOTAL.labels(name, "selector_fallback", "success").inc()
        SCRAPE_KEYWORDS.labels(name).inc(len(results))
        logger.info("Scraped %s: %d results in %.1fs", name, len(results), duration)
    else:
        logger.warning("Scrape returned no results for %s after %.1fs", name, duration)
    return results


async def _scrape_with_scrapegraph_method(
    name: str,
    config: SourceConfig,
    run_id: str,
) -> List[Dict[str, Any]]:
    started = time.monotonic()
    try:
        results = await scrape_with_scrapegraph(name, config)
    except Exception as exc:
        duration = time.monotonic() - started
        SCRAPE_DURATION.labels(name).observe(duration)
        SCRAPE_METHOD_TOTAL.labels(name, "scrapegraph", "failure").inc()
        logger.info(
            "ScrapeGraphAI failed source=%s run_id=%s duration=%.1fs error=%s",
            name,
            run_id,
            duration,
            exc,
        )
        raise

    duration = time.monotonic() - started
    SCRAPE_DURATION.labels(name).observe(duration)
    if results:
        SCRAPE_METHOD_TOTAL.labels(name, "scrapegraph", "success").inc()
        SCRAPE_TOTAL.labels(name, "success").inc()
        SCRAPE_KEYWORDS.labels(name).inc(len(results))
        logger.info(
            "ScrapeGraphAI scraped source=%s run_id=%s count=%d duration=%.1fs",
            name,
            run_id,
            len(results),
            duration,
        )
    return results


async def _scrape_source_chain(
    playwright,
    name: str,
    config: SourceConfig,
    profile: ScrapeProfile,
    run_id: str,
) -> tuple[List[Dict[str, Any]], str | None, str | None]:
    scrapegraph_error: str | None = None
    try:
        results = await _scrape_with_scrapegraph_method(name, config, run_id)
        if results:
            return results, "scrapegraph", None
        scrapegraph_error = "No ScrapeGraphAI trend items collected"
    except Exception as exc:
        scrapegraph_error = str(exc)

    SCRAPE_FALLBACK_TOTAL.labels(name, "scrapegraph", "selector_fallback").inc()
    try:
        selector_results = await _scrape_with_circuit_breaker(playwright, name, config, profile)
        if selector_results:
            for result in selector_results:
                result.setdefault("method", "selector_fallback")
            return selector_results, "selector_fallback", scrapegraph_error
        return [], None, "No selector trend items collected"
    except Exception as exc:
        if scrapegraph_error:
            return [], None, f"scrapegraph: {scrapegraph_error}; selector_fallback: {exc}"
        return [], None, str(exc)


def _extract_rss_signals(xml_text: str) -> List[Dict[str, Any]]:
    root = ET.fromstring(xml_text)
    items = root.findall(".//item")
    signals: List[Dict[str, Any]] = []
    for index, item in enumerate(items[: max(TOP_K * 3, 10)]):
        title = (item.findtext("title") or "").strip()
        if not title:
            continue
        keyword = normalize_text(title)
        if not keyword:
            continue
        score = max(10, 100 - (index * 3))
        signals.append(
            {
                "source": "google_trends_rss",
                "keyword": keyword,
                "engagement_score": score,
                "category": categorize(keyword),
            }
        )
    return signals


async def _fetch_rss_signals() -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(TREND_RSS_URL)
        response.raise_for_status()
    return _extract_rss_signals(response.text)


async def _gather_trends() -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if STUB_ONLY:
        signals = _stub_signals()
        return signals, {
            "mode": "stub",
            "sources_succeeded": ["stub_seed"],
            "sources_failed": {},
            "source_methods": {"stub_seed": "stub"},
            "sources_skipped": [],
            "fallback_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
        }

    validate_public_only_config()
    run_id = uuid4().hex[:12]
    rng = _new_rng()
    aggregated: List[Dict[str, Any]] = []
    sources_succeeded: List[str] = []
    sources_failed: Dict[str, str] = {}
    source_methods: Dict[str, str] = {}
    sources_skipped: List[str] = []
    allowed_source_names: List[str] = []
    fallback_count = 0

    try:
        async with async_playwright() as pw:
            tasks = []
            for name in build_scrape_plan(rng=rng):
                config = PLATFORM_CONFIG[name]
                if not scraper_circuit_breaker.allow_request(name):
                    logger.warning("Circuit breaker OPEN for %s - skipping scrape", name)
                    SCRAPE_TOTAL.labels(name, "circuit_open").inc()
                    SCRAPE_METHOD_TOTAL.labels(name, "circuit", "skipped").inc()
                    sources_failed[name] = "Circuit breaker open"
                    source_methods[name] = "failed"
                    sources_skipped.append(name)
                    continue
                allowed_source_names.append(name)
                profile = build_scrape_profile(config, rng)
                tasks.append(_scrape_source_chain(pw, name, config, profile, run_id))
            results = await asyncio.gather(*tasks, return_exceptions=True) if tasks else []
    except PublicOnlyConfigError:
        raise
    except Exception as exc:
        for name in allowed_source_names:
            scraper_circuit_breaker.record_failure(name)
        sources_failed["playwright"] = str(exc)
        source_methods["playwright"] = "failed"
        logger.warning("Playwright trend collection failed: %s", exc)
    else:
        for name, result in zip(allowed_source_names, results):
            if isinstance(result, Exception):
                scraper_circuit_breaker.record_failure(name)
                sources_failed[name] = str(result)
                source_methods[name] = "failed"
                logger.warning("Trend scrape failed for %s: %s", name, result)
                continue
            source_results, method, upstream_error = result
            if upstream_error:
                fallback_count += 1
            if source_results and method:
                scraper_circuit_breaker.record_success(name)
                aggregated.extend(source_results)
                sources_succeeded.append(name)
                source_methods[name] = method
                continue
            scraper_circuit_breaker.record_failure(name)
            SCRAPE_TOTAL.labels(name, "failure").inc()
            SCRAPE_METHOD_TOTAL.labels(name, "selector_fallback", "failure").inc()
            source_methods[name] = "failed"
            sources_failed[name] = upstream_error or "No trend items collected"

    try:
        rss_signals = await _fetch_rss_signals()
        if rss_signals:
            for signal in rss_signals:
                signal.setdefault("method", "rss_fallback")
            aggregated.extend(rss_signals)
            sources_succeeded.append("google_trends_rss")
            source_methods["google_trends_rss"] = "rss_fallback"
            SCRAPE_TOTAL.labels("google_trends_rss", "success").inc()
            SCRAPE_METHOD_TOTAL.labels("google_trends_rss", "rss_fallback", "success").inc()
            SCRAPE_KEYWORDS.labels("google_trends_rss").inc(len(rss_signals))
            if any(method == "failed" for method in source_methods.values()):
                fallback_count += 1
        else:
            sources_failed["google_trends_rss"] = "No RSS trend items collected"
            source_methods["google_trends_rss"] = "failed"
            SCRAPE_METHOD_TOTAL.labels("google_trends_rss", "rss_fallback", "failure").inc()
    except Exception as exc:
        sources_failed["google_trends_rss"] = str(exc)
        source_methods["google_trends_rss"] = "failed"
        SCRAPE_METHOD_TOTAL.labels("google_trends_rss", "rss_fallback", "failure").inc()

    if not aggregated:
        fallback = _stub_signals()
        logger.warning("Live trend collection fell back to stub data: %s", sources_failed)
        return fallback, {
            "mode": "fallback_stub",
            "sources_succeeded": sources_succeeded,
            "sources_failed": sources_failed,
            "source_methods": source_methods,
            "sources_skipped": sources_skipped,
            "fallback_count": fallback_count,
            "failed_count": len(sources_failed),
            "skipped_count": len(sources_skipped),
        }

    return aggregated, {
        "mode": "live",
        "sources_succeeded": sources_succeeded,
        "sources_failed": sources_failed,
        "source_methods": source_methods,
        "sources_skipped": sources_skipped,
        "fallback_count": fallback_count,
        "failed_count": len(sources_failed),
        "skipped_count": len(sources_skipped),
    }


async def refresh_trends() -> Dict[str, Any]:
    """Scrape all platforms and persist top signals."""
    started_at = datetime.utcnow()
    signals, gather_meta = await _gather_trends()
    mode = str(gather_meta.get("mode") or ("stub" if STUB_ONLY else "live"))

    if not signals:
        _refresh_status.update(
            {
                "last_started_at": started_at,
                "last_finished_at": datetime.utcnow(),
                "last_mode": mode,
                "sources_succeeded": gather_meta.get("sources_succeeded", []),
                "sources_failed": gather_meta.get("sources_failed", {}),
                "source_methods": gather_meta.get("source_methods", {}),
                "sources_skipped": gather_meta.get("sources_skipped", []),
                "signals_collected": 0,
                "signals_persisted": 0,
                "failed_count": gather_meta.get("failed_count", 0),
                "fallback_count": gather_meta.get("fallback_count", 0),
                "skipped_count": gather_meta.get("skipped_count", 0),
            }
        )
        return get_refresh_status()

    persisted = 0
    async with get_session() as session:
        for source in {signal["source"] for signal in signals}:
            top_candidates = sorted(
                [signal for signal in signals if signal["source"] == source],
                key=lambda signal: signal["engagement_score"],
                reverse=True,
            )
            seen_keywords: set[str] = set()
            top_signals: List[Dict[str, Any]] = []
            for signal in top_candidates:
                dedupe_key = normalize_text(str(signal.get("keyword") or ""))
                if not dedupe_key or dedupe_key in seen_keywords:
                    continue
                seen_keywords.add(dedupe_key)
                top_signals.append(signal)
                if len(top_signals) >= TOP_K:
                    break

            for signal in top_signals:
                session.add(
                    TrendSignal(
                        source=signal["source"],
                        keyword=signal["keyword"],
                        engagement_score=signal["engagement_score"],
                        category=signal["category"],
                        timestamp=datetime.utcnow(),
                    )
                )
                SCRAPE_PERSISTED.labels(signal["source"]).inc()
                persisted += 1
        await session.commit()

    _refresh_status.update(
        {
            "last_started_at": started_at,
            "last_finished_at": datetime.utcnow(),
            "last_mode": mode,
            "sources_succeeded": gather_meta.get("sources_succeeded", []),
            "sources_failed": gather_meta.get("sources_failed", {}),
            "source_methods": gather_meta.get("source_methods", {}),
            "sources_skipped": gather_meta.get("sources_skipped", []),
            "signals_collected": len(signals),
            "signals_persisted": persisted,
            "failed_count": gather_meta.get("failed_count", 0),
            "fallback_count": gather_meta.get("fallback_count", 0),
            "skipped_count": gather_meta.get("skipped_count", 0),
        }
    )
    return get_refresh_status()


async def get_live_trends(
    category: str | None = None,
    source: str | None = None,
    lookback_hours: int = DEFAULT_LOOKBACK_HOURS,
    per_group_limit: int = TOP_K,
) -> Dict[str, List[Dict[str, Any]]]:
    lookback_hours = max(1, lookback_hours)
    per_group_limit = min(max(1, per_group_limit), MAX_LIVE_TRENDS_PER_GROUP)
    cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)

    async with get_session() as session:
        stmt = select(TrendSignal).where(TrendSignal.timestamp >= cutoff)
        if category:
            stmt = stmt.where(TrendSignal.category == category)
        if source:
            stmt = stmt.where(TrendSignal.source == source)
        result = await session.exec(stmt)
        rows = result.all()

    deduped_rows: dict[tuple[str, str, str], TrendSignal] = {}
    for row in rows:
        keyword = normalize_text(row.keyword)
        if not keyword:
            continue
        key = (row.category, row.source, keyword)
        existing = deduped_rows.get(key)
        if (
            existing is None
            or row.engagement_score > existing.engagement_score
            or (row.engagement_score == existing.engagement_score and row.timestamp > existing.timestamp)
        ):
            deduped_rows[key] = row

    sorted_rows = sorted(
        deduped_rows.values(),
        key=lambda row: (row.category, -row.engagement_score, -row.timestamp.timestamp()),
    )

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in sorted_rows:
        if len(grouped[row.category]) >= per_group_limit:
            continue
        grouped[row.category].append(
            {
                "source": row.source,
                "keyword": row.keyword,
                "engagement_score": row.engagement_score,
                "timestamp": row.timestamp.isoformat(),
            }
        )
    return grouped


async def _periodic_refresh_wrapper() -> None:
    try:
        await refresh_trends()
    except Exception as exc:
        logger.error("Scheduled trend refresh failed: %s", exc)


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(_periodic_refresh_wrapper, "interval", hours=SCRAPE_INTERVAL_HOURS)
    scheduler.start()
    logger.info(
        "Trend ingestion scheduler started interval_hours=%s stub=%s",
        SCRAPE_INTERVAL_HOURS,
        STUB_ONLY,
    )
