import asyncio
import os
import random
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from playwright.async_api import async_playwright
from sqlmodel import select

from ..common.database import get_session
from ..models import TrendSignal

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/118.0",
]

STOPWORDS = {"the", "and", "a", "of", "to", "in"}
EMOJI_RE = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)

SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
PLAYWRIGHT_PROXY = os.getenv("PLAYWRIGHT_PROXY")
TOP_K = 5

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


async def _scrape_source(playwright, source: str, url: str, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
    ua = random.choice(USER_AGENTS)
    proxy = {"server": PLAYWRIGHT_PROXY} if PLAYWRIGHT_PROXY else None
    browser = await playwright.chromium.launch(headless=True, proxy=proxy)
    context = await browser.new_context(user_agent=ua)
    page = await context.new_page()
    await page.goto(url)
    items = await page.query_selector_all(selectors["item"])
    results: List[Dict[str, Any]] = []
    for item in items[:TOP_K]:
        title_el = await item.query_selector(selectors["title"])
        hashtag_el = await item.query_selector(selectors["hashtags"])
        likes_el = await item.query_selector(selectors["likes"])
        shares_el = await item.query_selector(selectors["shares"])
        comments_el = await item.query_selector(selectors["comments"])
        if not title_el:
            continue
        title = await title_el.inner_text()
        hashtags = await hashtag_el.inner_text() if hashtag_el else ""
        likes = int((await likes_el.inner_text()) or 0) if likes_el else 0
        shares = int((await shares_el.inner_text()) or 0) if shares_el else 0
        comments = int((await comments_el.inner_text()) or 0) if comments_el else 0
        keyword = normalize_text(f"{title} {hashtags}")
        engagement = compute_engagement(likes, shares, comments)
        results.append(
            {
                "source": source,
                "keyword": keyword,
                "engagement_score": engagement,
                "category": categorize(keyword),
            }
        )
    await browser.close()
    return results


PLATFORM_CONFIG = {
    "tiktok": {
        "url": "https://www.tiktok.com/foryou",
        "selectors": {
            "item": "div.item",
            "title": ".title",
            "hashtags": ".hashtags",
            "likes": ".likes",
            "shares": ".shares",
            "comments": ".comments",
        },
    },
    "instagram": {
        "url": "https://www.instagram.com/explore",
        "selectors": {
            "item": "div.item",
            "title": ".title",
            "hashtags": ".hashtags",
            "likes": ".likes",
            "shares": ".shares",
            "comments": ".comments",
        },
    },
    "twitter": {
        "url": "https://twitter.com/explore",
        "selectors": {
            "item": "div.item",
            "title": ".title",
            "hashtags": ".hashtags",
            "likes": ".likes",
            "shares": ".shares",
            "comments": ".comments",
        },
    },
    "etsy": {
        "url": "https://www.etsy.com/trending-items",
        "selectors": {
            "item": "div.item",
            "title": ".title",
            "hashtags": ".hashtags",
            "likes": ".likes",
            "shares": ".shares",
            "comments": ".comments",
        },
    },
}


async def refresh_trends() -> None:
    """Scrape all platforms and persist top signals."""
    async with async_playwright() as pw:
        tasks = [
            _scrape_source(pw, name, cfg["url"], cfg["selectors"])
            for name, cfg in PLATFORM_CONFIG.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    signals: List[Dict[str, Any]] = []
    for res in results:
        if isinstance(res, list):
            signals.extend(res)

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
                ts = TrendSignal(
                    source=sig["source"],
                    keyword=sig["keyword"],
                    engagement_score=sig["engagement_score"],
                    category=sig["category"],
                    timestamp=datetime.utcnow(),
                )
                session.add(ts)
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


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(refresh_trends, "interval", hours=SCRAPE_INTERVAL_HOURS)
    scheduler.start()
