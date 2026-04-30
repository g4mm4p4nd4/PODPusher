import asyncio
import logging
import os
import random
import re
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any, Dict, List, Sequence
from uuid import uuid4

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from playwright.async_api import async_playwright
from sqlmodel import select

from ..common.database import get_session
from ..common.observability import Counter, Histogram
from ..common.time import utcnow
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
TEXT_FALLBACK_STOPWORDS = {
    "about",
    "access",
    "actions",
    "ads",
    "all",
    "api",
    "blog",
    "browse",
    "business",
    "cart",
    "contact",
    "content",
    "cookie",
    "create",
    "english",
    "find",
    "help",
    "home",
    "inspiration",
    "location",
    "login",
    "main",
    "more",
    "popular",
    "privacy",
    "profile",
    "search",
    "service",
    "settings",
    "shop",
    "sign",
    "skip",
    "terms",
    "tools",
    "trend",
    "trending",
    "trends",
    "upload",
}
NAVIGATION_OR_TECH_TOKENS = {
    "account",
    "advertising",
    "amazon",
    "arrow",
    "black",
    "cart",
    "center",
    "checkout",
    "comment",
    "desktop",
    "explore",
    "facebook",
    "fff",
    "griditemroot",
    "instagram",
    "javascript",
    "navbar",
    "navarrow",
    "nprogress",
    "placeholder",
    "react",
    "sponsored",
    "tiktok",
    "twitter",
    "white",
}
POD_ORIENTED_TERMS = {
    "art",
    "bag",
    "blanket",
    "cap",
    "canvas",
    "coffee",
    "cup",
    "decor",
    "drink",
    "fascinator",
    "gift",
    "hat",
    "hoodie",
    "interior",
    "jewelry",
    "mug",
    "party",
    "pillow",
    "poster",
    "print",
    "shirt",
    "sticker",
    "style",
    "sweatshirt",
    "tea",
    "tee",
    "tote",
    "tumbler",
    "wall",
    "water bottle",
    "wedding",
}
STRONG_POD_TERMS = {
    "bag",
    "blanket",
    "cap",
    "canvas",
    "decor",
    "fascinator",
    "hat",
    "hoodie",
    "jewelry",
    "mug",
    "pillow",
    "poster",
    "print",
    "shirt",
    "sticker",
    "sweatshirt",
    "tee",
    "tote",
    "tumbler",
    "wall art",
    "water bottle",
}
WEAK_PUBLIC_SOURCES_REQUIRE_POD = {"amazon", "google_trends_rss", "pinterest"}
NON_POD_KEYWORD_MARKERS = {
    "appetizer",
    "available",
    "earthquake",
    "gift basket",
    "heels",
    "lift style",
    "nail art",
    "near me",
    "photography",
    "postpartum",
    "present",
    "underwear",
}
AMAZON_LEADING_NOISE_TERMS = {
    "ankis",
    "ecosmart",
    "frida",
    "hanes",
    "men",
    "mens",
    "s",
    "women",
    "womens",
}
RSS_NEWS_NOISE_TERMS = {
    "injury",
    "playoffs",
    "roster",
    "schedule",
    "score",
    "standings",
    "trade",
}
BLOCKED_PAGE_MARKERS = (
    "access denied",
    "are you a robot",
    "captcha",
    "enable javascript and cookies",
    "enable js and disable",
    "javascript is not available",
    "login?redirect",
    "robot check",
    "unusual traffic",
)

SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
PLAYWRIGHT_PROXY = os.getenv("PLAYWRIGHT_PROXY")
TOP_K = int(os.getenv("TREND_INGESTION_TOP_K", "5"))
SCRAPER_TIMEOUT_MS = int(os.getenv("TREND_INGESTION_TIMEOUT_MS", "15000"))
STUB_ONLY = os.getenv("TREND_INGESTION_STUB", "0").lower() in {"1", "true", "yes"}
TREND_RSS_URL = os.getenv(
    "TREND_INGESTION_RSS_URL", "https://trends.google.com/trending/rss?geo=US"
)
RSS_FALLBACK_ENABLED = os.getenv("TREND_INGESTION_RSS_FALLBACK", "1").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
ALLOW_STUB_FALLBACK = os.getenv("TREND_INGESTION_ALLOW_STUB_FALLBACK", "1").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
DEFAULT_LOOKBACK_HOURS = int(os.getenv("TREND_INGESTION_LOOKBACK_HOURS", "72"))
MAX_LIVE_TRENDS_PER_GROUP = int(os.getenv("TREND_INGESTION_MAX_LIVE_PER_GROUP", "50"))
MAX_SOURCE_URLS = int(os.getenv("TREND_INGESTION_MAX_SOURCE_URLS", "2"))
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
    "source_diagnostics": {},
    "sources_blocked": [],
    "signals_collected": 0,
    "signals_persisted": 0,
    "failed_count": 0,
    "fallback_count": 0,
    "skipped_count": 0,
    "blocked_count": 0,
}


class SourceBlockedError(RuntimeError):
    """Raised when a public page is login, bot, captcha, or access gated."""


def normalize_text(text: str) -> str:
    """Lowercase text, remove emojis and stopwords."""
    text = EMOJI_RE.sub("", text).lower()
    words = [word for word in re.split(r"\W+", text) if word and word not in STOPWORDS]
    return " ".join(words)


def _contains_term(keyword: str, term: str) -> bool:
    if " " in term:
        return f" {term} " in f" {keyword} "
    return term in keyword.split()


def _contains_pod_signal(keyword: str) -> bool:
    return any(_contains_term(keyword, term) for term in POD_ORIENTED_TERMS)


def _contains_strong_pod_signal(keyword: str) -> bool:
    return any(_contains_term(keyword, term) for term in STRONG_POD_TERMS)


def _looks_like_noise_keyword(
    keyword: str, *, method: str | None = None, source: str | None = None
) -> bool:
    words = keyword.split()
    if not words:
        return True
    compact = "".join(words)
    if any(marker in keyword for marker in NON_POD_KEYWORD_MARKERS):
        return True
    if re.fullmatch(r"[a-f0-9]{6,8}", compact):
        return True
    if re.fullmatch(r"[a-z]*\d+[a-z\d]*", compact) and len(words) <= 2:
        return True
    if any(word in NAVIGATION_OR_TECH_TOKENS for word in words):
        return True
    if len(words) == 1 and words[0] in TEXT_FALLBACK_STOPWORDS:
        return True
    if method == "rss_fallback":
        if any(term in words for term in RSS_NEWS_NOISE_TERMS):
            return True
        if not _contains_strong_pod_signal(keyword):
            return True
    if source in WEAK_PUBLIC_SOURCES_REQUIRE_POD:
        if not _contains_strong_pod_signal(keyword):
            return True
    return False


def _condense_keyword(keyword: str, source: str) -> str:
    words = keyword.split()
    if source == "amazon":
        while len(words) > 1 and words[0] in AMAZON_LEADING_NOISE_TERMS:
            words = words[1:]
        keyword = " ".join(words)
    if len(words) <= 8:
        return keyword
    if source == "amazon":
        product_terms = {term for term in POD_ORIENTED_TERMS if " " not in term}
        for index, word in enumerate(words):
            if word in product_terms:
                start = max(0, index - 2)
                condensed_words = words[start : index + 5]
                while (
                    len(condensed_words) > 1
                    and condensed_words[0] in AMAZON_LEADING_NOISE_TERMS
                ):
                    condensed_words = condensed_words[1:]
                return " ".join(condensed_words)
    return " ".join(words[:8])


def _sanitize_reason(reason: Any) -> str:
    text = str(reason or "").replace("\r", " ").replace("\n", " ")
    if "Executable doesn't exist" in text and "ms-playwright" in text:
        text = "Playwright browser executable unavailable"
    if "╔" in text:
        text = text.split("╔", 1)[0].strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text[:280] if len(text) > 280 else text


def _is_blocked_page(
    url: str, title: str, body_text: str, status: int | None = None
) -> bool:
    combined = " ".join([url, title, body_text[:3000]]).lower()
    if status in {401, 403, 429}:
        return True
    if any(marker in combined for marker in BLOCKED_PAGE_MARKERS):
        return True
    login_url_markers = ("/login", "/accounts/login", "/i/flow/login")
    return any(marker in url.lower() for marker in login_url_markers)


def compute_engagement(likes: int, shares: int, comments: int) -> int:
    return likes + shares + comments


CATEGORIES: Dict[str, List[str]] = {
    "animals": ["cat", "dog", "pet", "animal", "paw", "fur"],
    "activism": ["protest", "climate", "justice", "rights", "awareness"],
    "sports": ["game", "soccer", "basketball", "tennis", "pickleball", "baseball"],
    "apparel": ["shirt", "tee", "hoodie", "sweatshirt", "hat", "cap"],
    "drinkware": ["mug", "tumbler", "cup", "coffee"],
    "home_decor": ["decor", "wall art", "poster", "print", "canvas"],
    "bags": ["tote", "bag", "backpack"],
    "gifts": ["gift", "birthday", "mother", "father", "teacher", "holiday"],
}

CATEGORY_ALIASES = {
    "pet": "animals",
    "pets": "animals",
    "animal": "animals",
    "climate": "activism",
    "awareness": "activism",
    "apparel": "apparel",
    "clothing": "apparel",
    "tshirts": "apparel",
    "t shirts": "apparel",
    "mugs": "drinkware",
    "drinkware": "drinkware",
    "home": "home_decor",
    "home decor": "home_decor",
    "wall art": "home_decor",
    "bags": "bags",
    "gifting": "gifts",
    "gift": "gifts",
}


def categorize(keyword: str) -> str:
    for category, keys in CATEGORIES.items():
        if any(key in keyword for key in keys):
            return category
    return "other"


def normalize_category(raw_category: str | None, keyword: str) -> str:
    cleaned = normalize_text(str(raw_category or "")).replace(" ", "_")
    alias = CATEGORY_ALIASES.get(cleaned.replace("_", " "))
    if alias:
        return alias
    if cleaned in CATEGORIES:
        return cleaned
    inferred = categorize(keyword)
    return inferred if inferred != "other" else "uncategorized"


def _signal_confidence(
    method: str | None, keyword: str, engagement_score: int
) -> float:
    base = {
        "scrapegraph": 0.86,
        "selector_fallback": 0.78,
        "rss_fallback": 0.72,
        "stub": 0.58,
    }.get(method or "", 0.68)
    word_count = len(keyword.split())
    if word_count >= 2:
        base += 0.04
    if engagement_score > 0:
        base += 0.03
    return round(min(base, 0.94), 2)


def normalize_signal(
    signal: Dict[str, Any],
    *,
    default_source: str | None = None,
    default_method: str | None = None,
) -> Dict[str, Any] | None:
    keyword = normalize_text(str(signal.get("keyword") or signal.get("term") or ""))
    method = str(signal.get("method") or default_method or "unknown")
    source = str(signal.get("source") or default_source or "unknown")
    keyword = _condense_keyword(keyword, source)
    if len(keyword) < 3:
        return None
    if re.fullmatch(r"\d+(?:\.\d+)?[km]?", keyword):
        return None
    if _looks_like_noise_keyword(keyword, method=method, source=source):
        return None
    raw_score = signal.get("engagement_score") or signal.get("score") or 0
    if isinstance(raw_score, str):
        engagement_score = _parse_metric(raw_score)
    else:
        try:
            engagement_score = int(raw_score)
        except (TypeError, ValueError):
            engagement_score = 0
    engagement_score = max(0, engagement_score)
    category = normalize_category(str(signal.get("category") or ""), keyword)
    confidence = float(
        signal.get("confidence")
        or _signal_confidence(method, keyword, engagement_score)
    )
    return {
        **signal,
        "source": source,
        "keyword": keyword,
        "engagement_score": engagement_score,
        "category": category,
        "method": method,
        "provenance": {
            "source": source,
            "is_estimated": method in {"rss_fallback", "stub", "unknown"},
            "updated_at": utcnow().isoformat(),
            "confidence": confidence,
        },
    }


def _stub_signals() -> List[Dict[str, Any]]:
    samples = [
        ("tiktok", "funny cat dance", 4200),
        ("instagram", "minimalist home decor", 2750),
        ("twitter", "eco friendly tips", 1900),
        ("etsy", "personalised gift ideas", 1650),
    ]
    signals: List[Dict[str, Any]] = []
    for source, phrase, engagement in samples:
        signal = normalize_signal(
            {
                "source": source,
                "keyword": phrase,
                "engagement_score": engagement,
            },
            default_method="stub",
        )
        if signal:
            signals.append(signal)
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
        "source_diagnostics": dict(_refresh_status.get("source_diagnostics", {})),
        "sources_blocked": list(_refresh_status.get("sources_blocked", [])),
        "signals_collected": int(_refresh_status.get("signals_collected", 0)),
        "signals_persisted": int(_refresh_status.get("signals_persisted", 0)),
        "failed_count": int(_refresh_status.get("failed_count", 0)),
        "fallback_count": int(_refresh_status.get("fallback_count", 0)),
        "skipped_count": int(_refresh_status.get("skipped_count", 0)),
        "blocked_count": int(_refresh_status.get("blocked_count", 0)),
    }


def _new_rng() -> random.Random:
    if RANDOM_SEED is None:
        return random.Random()
    try:
        seed: int | str = int(RANDOM_SEED)
    except ValueError:
        seed = RANDOM_SEED
    return random.Random(seed)


def build_scrape_plan(
    source_names: Sequence[str] | None = None, rng: random.Random | None = None
) -> List[str]:
    names = list(source_names or PLATFORM_CONFIG.keys())
    active_rng = rng or _new_rng()
    active_rng.shuffle(names)
    return names


def build_scrape_profile(
    config: SourceConfig, rng: random.Random | None = None
) -> ScrapeProfile:
    active_rng = rng or _new_rng()
    configured_scrolls = int(getattr(config, "scroll_iterations", 0) or 0)
    return ScrapeProfile(
        user_agent=active_rng.choice(USER_AGENTS),
        viewport_width=active_rng.randint(1200, 1600),
        viewport_height=active_rng.randint(720, 1000),
        locale=active_rng.choice(["en-US", "en-GB"]),
        timezone_id=active_rng.choice(
            ["America/New_York", "America/Chicago", "America/Los_Angeles"]
        ),
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
            text = await _readable_node_text(node)
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
            text = await _readable_node_text(node)
            if text:
                values.append(text)
    return values


async def _readable_node_text(node) -> str:
    try:
        text = (await node.inner_text()).strip()
    except Exception:
        text = ""
    if text:
        return text
    for attribute in ("aria-label", "title", "alt"):
        try:
            value = await node.get_attribute(attribute)
        except Exception:
            value = None
        if value and value.strip():
            return value.strip()
    return ""


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


def _keyword_candidates_from_text(text: str, source: str) -> List[Dict[str, Any]]:
    if not text:
        return []
    cleaned = re.sub(r"#\s+", "#", text)
    candidates: List[Dict[str, Any]] = []
    seen: set[str] = set()

    for match in re.finditer(
        r"#\s*([A-Za-z][A-Za-z0-9_]{2,40})(?:\s+([\d,.]+[KMkm]?)\s+Posts?)?", cleaned
    ):
        keyword = match.group(1).replace("_", " ")
        score = (
            _parse_metric(match.group(2) or "")
            if match.group(2)
            else max(10, 100 - len(candidates))
        )
        normalized = normalize_text(keyword)
        if normalized and normalized not in seen:
            seen.add(normalized)
            candidates.append(
                {"source": source, "keyword": keyword, "engagement_score": score}
            )

    sentence_phrases = re.findall(
        r"\b([A-Z][A-Za-z0-9]+(?:[- ][A-Za-z0-9]+){1,5})(?=\s+[A-Z#]|\s*$)",
        cleaned,
    )
    cleaned = cleaned + "\n" + "\n".join(sentence_phrases)

    lines = re.split(r"[\n\r]+| {2,}|(?<=\d\sPosts)\s+", cleaned)
    for line in lines:
        phrase = " ".join(line.split()).strip(" -|•·")
        if not phrase or len(phrase) > 90:
            continue
        lower = phrase.lower()
        if any(
            token in lower
            for token in ["log in", "sign up", "privacy policy", "terms of service"]
        ):
            continue
        normalized = normalize_text(phrase)
        words = normalized.split()
        if not (2 <= len(words) <= 6):
            continue
        if any(word in TEXT_FALLBACK_STOPWORDS for word in words):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        candidates.append(
            {
                "source": source,
                "keyword": phrase,
                "engagement_score": max(10, 100 - len(candidates)),
            }
        )
        if len(candidates) >= TOP_K * 3:
            break
    return candidates


async def _extract_text_fallback_signals(page, source: str) -> List[Dict[str, Any]]:
    texts: List[str] = []
    for selector in [
        "h1",
        "h2",
        "h3",
        "a[href*='hashtag']",
        "a[href*='/explore/tags/']",
        "body",
    ]:
        try:
            values = await page.locator(selector).all_text_contents(timeout=3000)
        except Exception:
            values = []
        texts.extend(value for value in values if value)
    signals: List[Dict[str, Any]] = []
    for candidate in _keyword_candidates_from_text("\n".join(texts), source):
        signal = normalize_signal(candidate, default_method="selector_text_fallback")
        if signal:
            signals.append(signal)
    return signals


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
        response = await page.goto(
            config.url,
            wait_until="domcontentloaded",
            timeout=SCRAPER_TIMEOUT_MS,
        )
        try:
            await page.wait_for_selector(
                config.wait_for_selector, timeout=SCRAPER_TIMEOUT_MS
            )
        except Exception:
            pass
        try:
            await page.wait_for_load_state("load", timeout=SCRAPER_TIMEOUT_MS)
        except Exception:
            pass
        try:
            title = await page.title()
        except Exception:
            title = ""
        try:
            body_text = await page.locator("body").inner_text(timeout=3000)
        except Exception:
            body_text = ""
        status = response.status if response is not None else None
        if _is_blocked_page(page.url, title, body_text, status):
            raise SourceBlockedError(
                f"Public page blocked or login gated status={status} url={page.url}"
            )
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
            keyword = normalize_text(
                " ".join(filter(None, [title, " ".join(hashtags)]))
            )
            if not keyword:
                continue
            engagement = compute_engagement(
                _parse_metric(likes_text),
                _parse_metric(shares_text),
                _parse_metric(comments_text),
            )
            signal = normalize_signal(
                {
                    "source": name,
                    "keyword": keyword,
                    "engagement_score": engagement,
                },
                default_method="selector_fallback",
            )
            if signal:
                results.append(signal)
        if not results:
            results.extend(await _extract_text_fallback_signals(page, name))
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
        logger.error(
            "Scrape failed for %s after %.1fs: %s",
            name,
            duration,
            _sanitize_reason(exc),
        )
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
            _sanitize_reason(exc),
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
    errors: List[str] = []
    for index, url in enumerate(config.urls()[: max(1, MAX_SOURCE_URLS)]):
        candidate_config = replace(config, url=url, candidate_urls=None)
        scrapegraph_error: str | None = None
        try:
            results = await _scrape_with_scrapegraph_method(
                name, candidate_config, run_id
            )
            if results:
                return (
                    results,
                    "scrapegraph",
                    None if index == 0 else f"primary_url_empty; used {url}",
                )
            scrapegraph_error = f"{url}: No ScrapeGraphAI trend items collected"
        except Exception as exc:
            scrapegraph_error = f"{url}: {_sanitize_reason(exc)}"

        SCRAPE_FALLBACK_TOTAL.labels(name, "scrapegraph", "selector_fallback").inc()
        try:
            selector_results = await _scrape_with_circuit_breaker(
                playwright, name, candidate_config, profile
            )
            if selector_results:
                for result in selector_results:
                    result.setdefault("method", "selector_fallback")
                return selector_results, "selector_fallback", scrapegraph_error
            errors.append(
                f"scrapegraph: {scrapegraph_error}; selector_fallback: No selector trend items collected"
            )
        except SourceBlockedError as exc:
            return (
                [],
                "blocked",
                f"scrapegraph: {scrapegraph_error}; blocked: {_sanitize_reason(exc)}",
            )
        except Exception as exc:
            errors.append(
                f"scrapegraph: {scrapegraph_error}; selector_fallback: {_sanitize_reason(exc)}"
            )
    return [], None, " | ".join(errors[-3:]) or "No trend items collected"


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
        signal = normalize_signal(
            {
                "source": "google_trends_rss",
                "keyword": keyword,
                "engagement_score": score,
            },
            default_method="rss_fallback",
        )
        if signal:
            signals.append(signal)
    return signals


async def _fetch_rss_signals() -> List[Dict[str, Any]]:
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.get(TREND_RSS_URL)
        response.raise_for_status()
    return _extract_rss_signals(response.text)


def _diagnostic(
    *,
    status: str,
    method: str | None = None,
    collected: int = 0,
    persisted: int = 0,
    fallback_from: str | None = None,
    fallback_to: str | None = None,
    reason: str | None = None,
) -> Dict[str, Any]:
    return {
        "status": status,
        "method": method,
        "collected": collected,
        "persisted": persisted,
        "fallback_from": fallback_from,
        "fallback_to": fallback_to,
        "reason": reason,
        "updated_at": utcnow().isoformat(),
    }


def _normalize_signal_batch(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for signal in signals:
        normalized_signal = normalize_signal(signal)
        if normalized_signal:
            normalized.append(normalized_signal)
    return normalized


async def _gather_trends() -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if STUB_ONLY:
        signals = _stub_signals()
        return signals, {
            "mode": "stub",
            "sources_succeeded": ["stub_seed"],
            "sources_failed": {},
            "source_methods": {"stub_seed": "stub"},
            "sources_skipped": [],
            "source_diagnostics": {
                "stub_seed": _diagnostic(
                    status="success",
                    method="stub",
                    collected=len(signals),
                )
            },
            "sources_blocked": [],
            "fallback_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "blocked_count": 0,
        }

    validate_public_only_config()
    run_id = uuid4().hex[:12]
    rng = _new_rng()
    aggregated: List[Dict[str, Any]] = []
    sources_succeeded: List[str] = []
    sources_failed: Dict[str, str] = {}
    source_methods: Dict[str, str] = {}
    sources_skipped: List[str] = []
    source_diagnostics: Dict[str, Dict[str, Any]] = {}
    sources_blocked: List[str] = []
    allowed_source_names: List[str] = []
    fallback_count = 0

    try:
        async with async_playwright() as pw:
            tasks = []
            for name in build_scrape_plan(rng=rng):
                config = PLATFORM_CONFIG[name]
                if not scraper_circuit_breaker.allow_request(name):
                    logger.warning(
                        "Circuit breaker OPEN for %s - skipping scrape", name
                    )
                    SCRAPE_TOTAL.labels(name, "circuit_open").inc()
                    SCRAPE_METHOD_TOTAL.labels(name, "circuit", "skipped").inc()
                    sources_failed[name] = "Circuit breaker open"
                    source_methods[name] = "skipped"
                    sources_skipped.append(name)
                    sources_blocked.append(name)
                    source_diagnostics[name] = _diagnostic(
                        status="skipped",
                        method="circuit",
                        reason="Circuit breaker open",
                    )
                    continue
                allowed_source_names.append(name)
                profile = build_scrape_profile(config, rng)
                tasks.append(_scrape_source_chain(pw, name, config, profile, run_id))
            results = (
                await asyncio.gather(*tasks, return_exceptions=True) if tasks else []
            )
    except PublicOnlyConfigError:
        raise
    except Exception as exc:
        for name in allowed_source_names:
            scraper_circuit_breaker.record_failure(name)
        sources_failed["playwright"] = _sanitize_reason(exc)
        source_methods["playwright"] = "failed"
        source_diagnostics["playwright"] = _diagnostic(
            status="failed",
            method="playwright",
            reason=_sanitize_reason(exc),
        )
        logger.warning("Playwright trend collection failed: %s", _sanitize_reason(exc))
    else:
        for name, result in zip(allowed_source_names, results):
            if isinstance(result, Exception):
                scraper_circuit_breaker.record_failure(name)
                sources_failed[name] = _sanitize_reason(result)
                source_methods[name] = "failed"
                source_diagnostics[name] = _diagnostic(
                    status="failed",
                    method="unknown",
                    reason=_sanitize_reason(result),
                )
                logger.warning(
                    "Trend scrape failed for %s: %s", name, _sanitize_reason(result)
                )
                continue
            source_results, method, upstream_error = result
            if upstream_error:
                fallback_count += 1
            if method == "blocked":
                scraper_circuit_breaker.record_failure(name)
                source_methods[name] = "skipped"
                sources_failed[name] = (
                    upstream_error or "Public page blocked or login gated"
                )
                sources_skipped.append(name)
                sources_blocked.append(name)
                source_diagnostics[name] = _diagnostic(
                    status="skipped",
                    method="blocked",
                    reason=upstream_error or "Public page blocked or login gated",
                )
                continue
            if source_results and method:
                source_results = _normalize_signal_batch(source_results)
                if not source_results:
                    scraper_circuit_breaker.record_failure(name)
                    source_methods[name] = "failed"
                    sources_failed[name] = (
                        upstream_error or "No viable POD-oriented trend items collected"
                    )
                    source_diagnostics[name] = _diagnostic(
                        status="failed",
                        method=method,
                        reason=sources_failed[name],
                    )
                    continue
                scraper_circuit_breaker.record_success(name)
                aggregated.extend(source_results)
                sources_succeeded.append(name)
                source_methods[name] = method
                source_diagnostics[name] = _diagnostic(
                    status="success",
                    method=method,
                    collected=len(source_results),
                    fallback_from="scrapegraph" if upstream_error else None,
                    fallback_to=method if upstream_error else None,
                    reason=upstream_error,
                )
                continue
            scraper_circuit_breaker.record_failure(name)
            SCRAPE_TOTAL.labels(name, "failure").inc()
            SCRAPE_METHOD_TOTAL.labels(name, "selector_fallback", "failure").inc()
            source_methods[name] = "failed"
            sources_failed[name] = upstream_error or "No trend items collected"
            source_diagnostics[name] = _diagnostic(
                status="failed",
                method="selector_fallback",
                reason=upstream_error or "No trend items collected",
            )

    if RSS_FALLBACK_ENABLED:
        try:
            rss_signals = await _fetch_rss_signals()
            if rss_signals:
                rss_signals = _normalize_signal_batch(rss_signals)
                for signal in rss_signals:
                    signal.setdefault("method", "rss_fallback")
                aggregated.extend(rss_signals)
                sources_succeeded.append("google_trends_rss")
                source_methods["google_trends_rss"] = "rss_fallback"
                source_diagnostics["google_trends_rss"] = _diagnostic(
                    status="success",
                    method="rss_fallback",
                    collected=len(rss_signals),
                    fallback_from=(
                        "public_sources"
                        if any(method == "failed" for method in source_methods.values())
                        else None
                    ),
                    fallback_to="rss_fallback",
                )
                SCRAPE_TOTAL.labels("google_trends_rss", "success").inc()
                SCRAPE_METHOD_TOTAL.labels(
                    "google_trends_rss", "rss_fallback", "success"
                ).inc()
                SCRAPE_KEYWORDS.labels("google_trends_rss").inc(len(rss_signals))
                if any(method == "failed" for method in source_methods.values()):
                    fallback_count += 1
            else:
                sources_failed["google_trends_rss"] = "No RSS trend items collected"
                source_methods["google_trends_rss"] = "failed"
                source_diagnostics["google_trends_rss"] = _diagnostic(
                    status="failed",
                    method="rss_fallback",
                    reason="No RSS trend items collected",
                )
                SCRAPE_METHOD_TOTAL.labels(
                    "google_trends_rss", "rss_fallback", "failure"
                ).inc()
        except Exception as exc:
            sources_failed["google_trends_rss"] = str(exc)
            source_methods["google_trends_rss"] = "failed"
            source_diagnostics["google_trends_rss"] = _diagnostic(
                status="failed",
                method="rss_fallback",
                reason=str(exc),
            )
            SCRAPE_METHOD_TOTAL.labels(
                "google_trends_rss", "rss_fallback", "failure"
            ).inc()
    else:
        source_methods["google_trends_rss"] = "skipped"
        sources_skipped.append("google_trends_rss")
        source_diagnostics["google_trends_rss"] = _diagnostic(
            status="skipped",
            method="rss_fallback",
            reason="RSS fallback disabled",
        )
        SCRAPE_METHOD_TOTAL.labels("google_trends_rss", "rss_fallback", "skipped").inc()

    if not aggregated:
        fallback = _stub_signals() if ALLOW_STUB_FALLBACK else []
        mode = "fallback_stub" if fallback else "live_empty"
        if fallback:
            logger.warning(
                "Live trend collection fell back to stub data: %s", sources_failed
            )
        else:
            logger.warning(
                "Live trend collection returned no persisted candidates: %s",
                sources_failed,
            )
        return fallback, {
            "mode": mode,
            "sources_succeeded": sources_succeeded,
            "sources_failed": sources_failed,
            "source_methods": source_methods,
            "sources_skipped": sources_skipped,
            "source_diagnostics": source_diagnostics,
            "sources_blocked": sources_blocked,
            "fallback_count": fallback_count,
            "failed_count": len(
                [source for source in sources_failed if source not in sources_blocked]
            ),
            "skipped_count": len(sources_skipped),
            "blocked_count": len(sources_blocked),
        }

    return aggregated, {
        "mode": "live",
        "sources_succeeded": sources_succeeded,
        "sources_failed": sources_failed,
        "source_methods": source_methods,
        "sources_skipped": sources_skipped,
        "source_diagnostics": source_diagnostics,
        "sources_blocked": sources_blocked,
        "fallback_count": fallback_count,
        "failed_count": len(
            [source for source in sources_failed if source not in sources_blocked]
        ),
        "skipped_count": len(sources_skipped),
        "blocked_count": len(sources_blocked),
    }


async def refresh_trends() -> Dict[str, Any]:
    """Scrape all platforms and persist top signals."""
    started_at = utcnow()
    signals, gather_meta = await _gather_trends()
    mode = str(gather_meta.get("mode") or ("stub" if STUB_ONLY else "live"))

    if not signals:
        _refresh_status.update(
            {
                "last_started_at": started_at,
                "last_finished_at": utcnow(),
                "last_mode": mode,
                "sources_succeeded": gather_meta.get("sources_succeeded", []),
                "sources_failed": gather_meta.get("sources_failed", {}),
                "source_methods": gather_meta.get("source_methods", {}),
                "sources_skipped": gather_meta.get("sources_skipped", []),
                "source_diagnostics": gather_meta.get("source_diagnostics", {}),
                "sources_blocked": gather_meta.get("sources_blocked", []),
                "signals_collected": 0,
                "signals_persisted": 0,
                "failed_count": gather_meta.get("failed_count", 0),
                "fallback_count": gather_meta.get("fallback_count", 0),
                "skipped_count": gather_meta.get("skipped_count", 0),
                "blocked_count": gather_meta.get("blocked_count", 0),
            }
        )
        return get_refresh_status()

    persisted = 0
    diagnostics = dict(gather_meta.get("source_diagnostics", {}))
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
                normalized_signal = normalize_signal(signal)
                if not normalized_signal:
                    continue
                dedupe_key = normalized_signal["keyword"]
                if not dedupe_key or dedupe_key in seen_keywords:
                    continue
                seen_keywords.add(dedupe_key)
                top_signals.append(normalized_signal)
                if len(top_signals) >= TOP_K:
                    break

            for signal in top_signals:
                session.add(
                    TrendSignal(
                        source=signal["source"],
                        keyword=signal["keyword"],
                        engagement_score=signal["engagement_score"],
                        category=signal["category"],
                        timestamp=utcnow(),
                    )
                )
                SCRAPE_PERSISTED.labels(signal["source"]).inc()
                persisted += 1
            if source in diagnostics:
                diagnostics[source]["persisted"] = len(top_signals)
        await session.commit()

    _refresh_status.update(
        {
            "last_started_at": started_at,
            "last_finished_at": utcnow(),
            "last_mode": mode,
            "sources_succeeded": gather_meta.get("sources_succeeded", []),
            "sources_failed": gather_meta.get("sources_failed", {}),
            "source_methods": gather_meta.get("source_methods", {}),
            "sources_skipped": gather_meta.get("sources_skipped", []),
            "source_diagnostics": diagnostics,
            "sources_blocked": gather_meta.get("sources_blocked", []),
            "signals_collected": len(signals),
            "signals_persisted": persisted,
            "failed_count": gather_meta.get("failed_count", 0),
            "fallback_count": gather_meta.get("fallback_count", 0),
            "skipped_count": gather_meta.get("skipped_count", 0),
            "blocked_count": gather_meta.get("blocked_count", 0),
        }
    )
    return get_refresh_status()


async def get_live_trends(
    category: str | None = None,
    source: str | None = None,
    lookback_hours: int = DEFAULT_LOOKBACK_HOURS,
    per_group_limit: int = TOP_K,
    page: int = 1,
    page_size: int | None = None,
    sort_by: str = "engagement_score",
    sort_order: str = "desc",
    include_meta: bool = False,
) -> Dict[str, Any]:
    lookback_hours = max(1, lookback_hours)
    per_group_limit = min(max(1, per_group_limit), MAX_LIVE_TRENDS_PER_GROUP)
    page = max(1, page)
    page_size = min(max(1, page_size or per_group_limit), MAX_LIVE_TRENDS_PER_GROUP)
    cutoff = utcnow() - timedelta(hours=lookback_hours)

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
            or (
                row.engagement_score == existing.engagement_score
                and row.timestamp > existing.timestamp
            )
        ):
            deduped_rows[key] = row

    reverse = sort_order.lower() != "asc"
    if sort_by == "timestamp":
        sorted_rows = sorted(
            deduped_rows.values(), key=lambda row: row.timestamp, reverse=reverse
        )
    elif sort_by == "keyword":
        sorted_rows = sorted(
            deduped_rows.values(), key=lambda row: row.keyword.lower(), reverse=reverse
        )
    else:
        sorted_rows = sorted(
            deduped_rows.values(),
            key=lambda row: row.engagement_score,
            reverse=reverse,
        )

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    total_by_category: Dict[str, int] = defaultdict(int)
    offset = (page - 1) * page_size
    for row in sorted_rows:
        total_by_category[row.category] += 1
        category_index = total_by_category[row.category] - 1
        if category_index < offset:
            continue
        if len(grouped[row.category]) >= min(per_group_limit, page_size):
            continue
        grouped[row.category].append(
            {
                "source": row.source,
                "keyword": row.keyword,
                "category": row.category,
                "engagement_score": row.engagement_score,
                "timestamp": row.timestamp.isoformat(),
                "provenance": {
                    "source": row.source,
                    "is_estimated": row.source in {"google_trends_rss", "stub_seed"},
                    "updated_at": row.timestamp.isoformat(),
                    "confidence": 0.72 if row.source == "google_trends_rss" else 0.86,
                },
            }
        )
    if not include_meta:
        return grouped
    return {
        "items_by_category": grouped,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "per_group_limit": per_group_limit,
            "total": sum(total_by_category.values()),
            "total_by_category": dict(total_by_category),
            "sort_by": sort_by,
            "sort_order": "desc" if reverse else "asc",
        },
        "provenance": {
            "source": "trendsignal_table",
            "is_estimated": False,
            "updated_at": utcnow().isoformat(),
            "confidence": 0.86,
        },
    }


async def _periodic_refresh_wrapper() -> None:
    try:
        await refresh_trends()
    except Exception as exc:
        logger.error("Scheduled trend refresh failed: %s", exc)


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        _periodic_refresh_wrapper, "interval", hours=SCRAPE_INTERVAL_HOURS
    )
    scheduler.start()
    logger.info(
        "Trend ingestion scheduler started interval_hours=%s stub=%s",
        SCRAPE_INTERVAL_HOURS,
        STUB_ONLY,
    )
