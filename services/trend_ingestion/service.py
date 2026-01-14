import asyncio
import os
import random
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Sequence

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from playwright.async_api import async_playwright
from sqlmodel import select

from ..common.database import get_session
from ..models import TrendSignal
from .sources import PLATFORM_CONFIG, SourceConfig, SelectorSet

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/118.0",
]

STOPWORDS = {"the", "and", "a", "of", "to", "in"}
EMOJI_RE = re.compile(r"[𐀀-􏿿]", flags=re.UNICODE)

SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
PLAYWRIGHT_PROXY = os.getenv("PLAYWRIGHT_PROXY")
TOP_K = int(os.getenv("TREND_INGESTION_TOP_K", "5"))
SCRAPER_TIMEOUT_MS = int(os.getenv("TREND_INGESTION_TIMEOUT_MS", "15000"))
STUB_ONLY = os.getenv("TREND_INGESTION_STUB", "1").lower() in {"1", "true", "yes"}

scheduler = AsyncIOScheduler()


def normalize_text(text: str) -> str:
    """Lowercase text, remove emojis and stopwords."""
    text = EMOJI_RE.sub("", text).lower()
    words = [w for w in re.split(r"\W+", text) if w and w not in STOPWORDS]
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
        if any(k in keyword for k in keys):
            return category
    return "other"


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
    cleaned = value.strip().lower().replace(',', '')
    match = re.findall(r"\d+(?:\.\d+)?", cleaned)
    if not match:
        return 0
    base = float(match[0])
    if 'm' in cleaned:
        base *= 1_000_000
    elif 'k' in cleaned:
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


async def _gather_trends() -> List[Dict[str, Any]]:
    if STUB_ONLY:
        return []
    async with async_playwright() as pw:
        tasks = [
            _scrape_source(pw, name, config)
            for name, config in PLATFORM_CONFIG.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    aggregated: List[Dict[str, Any]] = []
    for result in results:
        if isinstance(result, list):
            aggregated.extend(result)
    return aggregated


async def refresh_trends() -> None:
    """Scrape all platforms and persist top signals."""
    signals = await _gather_trends()
    if not signals:
        return

    async with get_session() as session:
        for source in {s["source"] for s in signals}:
            top = sorted(
                [s for s in signals if s["source"] == source],
                key=lambda s: s["engagement_score"],
                reverse=True,
            )[:TOP_K]
            for sig in top:
                session.add(
                    TrendSignal(
                        source=sig["source"],
                        keyword=sig["keyword"],
                        engagement_score=sig["engagement_score"],
                        category=sig["category"],
                        timestamp=datetime.utcnow(),
                    )
                )
        await session.commit()


async def get_live_trends(category: str | None = None) -> Dict[str, List[Dict[str, Any]]]:
    async with get_session() as session:
        stmt = select(TrendSignal)
        if category:
            stmt = stmt.where(TrendSignal.category == category)
        result = await session.exec(stmt)
        rows = result.all()
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
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
    except Exception:
        # Avoid scheduler crash; detailed logging handled elsewhere.
        pass


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(_periodic_refresh_wrapper, "interval", hours=SCRAPE_INTERVAL_HOURS)
    scheduler.start()
