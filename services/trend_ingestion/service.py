import asyncio
import logging
import os
import random
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Sequence

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from playwright.async_api import async_playwright
from sqlmodel import select

try:
    from prometheus_client import Counter, Gauge
except ImportError:  # pragma: no cover - metrics are optional
    class _NoopMetric:  # pylint: disable=too-few-public-methods
        def labels(self, *_, **__):
            return self

        def inc(self, *_, **__):
            return None

        def set(self, *_, **__):
            return None

    def Counter(*_, **__):  # type: ignore
        return _NoopMetric()

    def Gauge(*_, **__):  # type: ignore
        return _NoopMetric()

try:
    import structlog
except ImportError:  # pragma: no cover
    structlog = None

from ..common.database import get_session
from ..models import TrendSignal
from .circuit_breaker import scraper_circuit_breaker
from .sources import PLATFORM_CONFIG, SourceConfig, SelectorSet

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
STUB_ONLY = os.getenv("TREND_INGESTION_STUB", "1").lower() in {"1", "true", "yes"}
TREND_RSS_URL = os.getenv("TREND_INGESTION_RSS_URL", "https://trends.google.com/trending/rss?geo=US")
DEFAULT_LOOKBACK_HOURS = int(os.getenv("TREND_INGESTION_LOOKBACK_HOURS", "72"))
MAX_LIVE_TRENDS_PER_GROUP = int(os.getenv("TREND_INGESTION_MAX_LIVE_PER_GROUP", "50"))

scheduler = AsyncIOScheduler()
logger = structlog.get_logger(__name__) if structlog else logging.getLogger(__name__)

SIGNALS_SCRAPED = Counter("trend_ingestion_signals_total", "Trend signals observed", ["mode"])
SCRAPE_FAILURES = Counter("trend_ingestion_failures_total", "Trend ingestion errors", ["mode"])
LAST_SCRAPE_COUNT = Gauge("trend_ingestion_last_count", "Signals stored during last refresh", ["mode"])

_refresh_status: Dict[str, Any] = {
    "last_started_at": None,
    "last_finished_at": None,
    "last_mode": "idle",
    "sources_succeeded": [],
    "sources_failed": {},
    "signals_collected": 0,
    "signals_persisted": 0,
}


def _log(level: str, event: str, **fields: Any) -> None:
    if structlog:
        getattr(logger, level)(event, **fields)
        return
    if fields:
        logger.log(getattr(logging, level.upper()), "%s %s", event, fields)
    else:
        logger.log(getattr(logging, level.upper()), event)


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
    stub: List[Dict[str, Any]] = []
    for source, phrase, engagement in samples:
        keyword = normalize_text(phrase)
        stub.append(
            {
                "source": source,
                "keyword": keyword,
                "engagement_score": engagement,
                "category": categorize(keyword),
            }
        )
    return stub


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
        "signals_collected": int(_refresh_status.get("signals_collected", 0)),
        "signals_persisted": int(_refresh_status.get("signals_persisted", 0)),
    }


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


async def _scrape_source(playwright, name: str, config: SourceConfig) -> List[Dict[str, Any]]:
    ua = random.choice(USER_AGENTS)
    proxy_settings = {"server": PLAYWRIGHT_PROXY} if PLAYWRIGHT_PROXY else None
    browser = await playwright.chromium.launch(headless=True, proxy=proxy_settings)
    context = await browser.new_context(user_agent=ua)
    page = await context.new_page()
    results: List[Dict[str, Any]] = []
    try:
        await page.goto(config.url, wait_until="networkidle", timeout=SCRAPER_TIMEOUT_MS)
        try:
            await page.wait_for_selector(config.wait_for_selector, timeout=SCRAPER_TIMEOUT_MS)
        except Exception:
            pass
        for _ in range(config.scroll_iterations):
            await page.mouse.wheel(0, 2400)
            await page.wait_for_timeout(1000)
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
        _log("info", "trend_ingestion.stub_data", count=len(signals))
        return signals, {
            "mode": "stub",
            "sources_succeeded": ["stub_seed"],
            "sources_failed": {},
        }

    aggregated: List[Dict[str, Any]] = []
    sources_succeeded: List[str] = []
    sources_failed: Dict[str, str] = {}
    allowed_source_names: List[str] = []

    try:
        async with async_playwright() as pw:
            source_names = list(PLATFORM_CONFIG.keys())
            tasks = []
            for name in source_names:
                if not scraper_circuit_breaker.allow_request(name):
                    sources_failed[name] = "Circuit breaker open"
                    _log("warning", "trend_ingestion.scrape_skipped_circuit_open", source=name)
                    continue
                allowed_source_names.append(name)
                tasks.append(_scrape_source(pw, name, PLATFORM_CONFIG[name]))
            results = await asyncio.gather(*tasks, return_exceptions=True) if tasks else []
        for name, result in zip(allowed_source_names, results):
            if isinstance(result, Exception):
                scraper_circuit_breaker.record_failure(name)
                sources_failed[name] = str(result)
                SCRAPE_FAILURES.labels(mode="live").inc()
                _log("warning", "trend_ingestion.scrape_failed", source=name, error=str(result))
                continue
            if result:
                scraper_circuit_breaker.record_success(name)
                aggregated.extend(result)
                sources_succeeded.append(name)
            else:
                scraper_circuit_breaker.record_failure(name)
                sources_failed[name] = "No trend items collected"
    except Exception as exc:
        for name in allowed_source_names:
            scraper_circuit_breaker.record_failure(name)
        sources_failed["playwright"] = str(exc)
        SCRAPE_FAILURES.labels(mode="live").inc()
        _log("warning", "trend_ingestion.playwright_failed", error=str(exc))

    try:
        rss_signals = await _fetch_rss_signals()
        if rss_signals:
            aggregated.extend(rss_signals)
            sources_succeeded.append("google_trends_rss")
        else:
            sources_failed["google_trends_rss"] = "No RSS trend items collected"
    except Exception as exc:
        sources_failed["google_trends_rss"] = str(exc)
        SCRAPE_FAILURES.labels(mode="live").inc()
        _log("warning", "trend_ingestion.rss_failed", error=str(exc))

    if not aggregated:
        fallback = _stub_signals()
        _log("warning", "trend_ingestion.live_fell_back_to_stub", failures=sources_failed)
        return fallback, {
            "mode": "fallback_stub",
            "sources_succeeded": sources_succeeded,
            "sources_failed": sources_failed,
        }

    _log(
        "info",
        "trend_ingestion.live_data_collected",
        count=len(aggregated),
        sources_succeeded=sources_succeeded,
    )
    return aggregated, {
        "mode": "live",
        "sources_succeeded": sources_succeeded,
        "sources_failed": sources_failed,
    }


async def refresh_trends() -> Dict[str, Any]:
    """Scrape all platforms and persist top signals."""
    started_at = datetime.utcnow()
    signals, gather_meta = await _gather_trends()
    mode = str(gather_meta.get("mode") or ("stub" if STUB_ONLY else "live"))

    if not signals:
        SCRAPE_FAILURES.labels(mode=mode).inc()
        LAST_SCRAPE_COUNT.labels(mode=mode).set(0)
        _refresh_status.update(
            {
                "last_started_at": started_at,
                "last_finished_at": datetime.utcnow(),
                "last_mode": mode,
                "sources_succeeded": gather_meta.get("sources_succeeded", []),
                "sources_failed": gather_meta.get("sources_failed", {}),
                "signals_collected": 0,
                "signals_persisted": 0,
            }
        )
        _log("warning", "trend_ingestion.no_signals", mode=mode)
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
            top: list[dict[str, Any]] = []
            for candidate in top_candidates:
                dedupe_key = normalize_text(str(candidate.get("keyword") or ""))
                if not dedupe_key or dedupe_key in seen_keywords:
                    continue
                seen_keywords.add(dedupe_key)
                top.append(candidate)
                if len(top) >= TOP_K:
                    break
            for signal in top:
                session.add(
                    TrendSignal(
                        source=signal["source"],
                        keyword=signal["keyword"],
                        engagement_score=signal["engagement_score"],
                        category=signal["category"],
                        timestamp=datetime.utcnow(),
                    )
                )
                persisted += 1
        await session.commit()

    SIGNALS_SCRAPED.labels(mode=mode).inc(persisted)
    LAST_SCRAPE_COUNT.labels(mode=mode).set(persisted)
    _refresh_status.update(
        {
            "last_started_at": started_at,
            "last_finished_at": datetime.utcnow(),
            "last_mode": mode,
            "sources_succeeded": gather_meta.get("sources_succeeded", []),
            "sources_failed": gather_meta.get("sources_failed", {}),
            "signals_collected": len(signals),
            "signals_persisted": persisted,
        }
    )

    if gather_meta.get("sources_failed"):
        _log(
            "warning",
            "trend_ingestion.refresh_partial",
            mode=mode,
            stored=persisted,
            failures=gather_meta.get("sources_failed"),
        )
    else:
        _log("info", "trend_ingestion.refresh_complete", mode=mode, stored=persisted)
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
        mode = "stub" if STUB_ONLY else "live"
        SCRAPE_FAILURES.labels(mode=mode).inc()
        _log("error", "trend_ingestion.refresh_failed", mode=mode, error=str(exc))


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(_periodic_refresh_wrapper, "interval", hours=SCRAPE_INTERVAL_HOURS)
    scheduler.start()
    _log(
        "info",
        "trend_ingestion.scheduler_started",
        interval_hours=SCRAPE_INTERVAL_HOURS,
        stub=STUB_ONLY,
    )
