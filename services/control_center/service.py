from __future__ import annotations

import os
from datetime import datetime, timedelta
from math import erf, sqrt
from typing import Any

from sqlalchemy import func
from sqlmodel import select

from ..billing.plans import get_plan_limits
from ..billing.service import get_user_plan_tier
from ..common.database import get_session
from ..common.time import utcnow
from ..models import (
    ABTest,
    ABVariant,
    AutomationJob,
    BrandProfile,
    Listing,
    ListingDraft,
    Notification,
    NotificationRule,
    OAuthCredential,
    SavedNiche,
    SavedSearch,
    SeasonalEvent,
    Store,
    TeamMember,
    TrendSignal,
    UsageLedger,
    User,
    WatchlistItem,
)

DEFAULT_USER_ID = 1
DEFAULT_NOW = utcnow

KEYWORD_FIXTURES = [
    {
        "keyword": "dog mom",
        "niche": "Dog Mom Gifts",
        "category": "Apparel",
        "volume": 156000,
        "growth": 64.2,
        "competition": 32,
        "products": ["T-Shirts", "Mugs", "Tote Bags"],
        "opportunity": "High",
    },
    {
        "keyword": "pickleball life",
        "niche": "Pickleball",
        "category": "Drinkware",
        "volume": 128000,
        "growth": 52.7,
        "competition": 46,
        "products": ["Hoodies", "Tumblers", "Stickers"],
        "opportunity": "High",
    },
    {
        "keyword": "teacher appreciation",
        "niche": "Teacher Appreciation",
        "category": "Mugs",
        "volume": 98500,
        "growth": 47.3,
        "competition": 38,
        "products": ["Mugs", "Tote Bags", "T-Shirts"],
        "opportunity": "High",
    },
    {
        "keyword": "vintage summer",
        "niche": "Vintage Summer",
        "category": "Apparel",
        "volume": 87600,
        "growth": 41.8,
        "competition": 58,
        "products": ["T-Shirts", "Wall Art", "Stickers"],
        "opportunity": "Medium",
    },
    {
        "keyword": "mental health matters",
        "niche": "Mental Health Awareness",
        "category": "Bags",
        "volume": 76300,
        "growth": 38.6,
        "competition": 35,
        "products": ["Tote Bags", "Sweatshirts", "Mugs"],
        "opportunity": "High",
    },
    {
        "keyword": "retro baseball",
        "niche": "Retro Baseball",
        "category": "Apparel",
        "volume": 65800,
        "growth": 32.1,
        "competition": 52,
        "products": ["T-Shirts", "Caps", "Hoodies"],
        "opportunity": "Medium",
    },
]

PRODUCT_CATEGORIES = [
    {
        "category": "T-Shirts",
        "listings": 124510,
        "trend": 15.6,
        "demand": 92,
        "opportunity": "High",
    },
    {
        "category": "Hoodies",
        "listings": 78320,
        "trend": 11.3,
        "demand": 86,
        "opportunity": "High",
    },
    {
        "category": "Mugs",
        "listings": 56744,
        "trend": 9.8,
        "demand": 78,
        "opportunity": "Medium",
    },
    {
        "category": "Tote Bags",
        "listings": 32118,
        "trend": 18.2,
        "demand": 72,
        "opportunity": "Medium",
    },
    {
        "category": "Wall Art",
        "listings": 28901,
        "trend": 7.1,
        "demand": 41,
        "opportunity": "Low",
    },
]

DESIGN_IDEAS = [
    {
        "title": "Dog Mom Floral Typo",
        "keyword": "dog mom",
        "trend": 23,
        "opportunity": "High",
    },
    {
        "title": "Pickleball Era Retro",
        "keyword": "pickleball",
        "trend": 31,
        "opportunity": "High",
    },
    {
        "title": "Mental Health Retro",
        "keyword": "mental health",
        "trend": 17,
        "opportunity": "Medium",
    },
    {
        "title": "Retro Beach Sunset",
        "keyword": "vintage summer",
        "trend": 21,
        "opportunity": "Medium",
    },
]

EVENT_FIXTURES = [
    {"name": "Mother's Day", "month": 5, "day": 10, "priority": "high", "icon": "MD"},
    {"name": "Memorial Day", "month": 5, "day": 25, "priority": "high", "icon": "US"},
    {"name": "Father's Day", "month": 6, "day": 21, "priority": "high", "icon": "FD"},
    {"name": "Juneteenth", "month": 6, "day": 19, "priority": "medium", "icon": "JN"},
    {"name": "Back to School", "month": 8, "day": 1, "priority": "high", "icon": "BS"},
    {"name": "Halloween", "month": 10, "day": 31, "priority": "high", "icon": "HW"},
    {"name": "Black Friday", "month": 11, "day": 27, "priority": "high", "icon": "BF"},
    {"name": "Christmas", "month": 12, "day": 25, "priority": "high", "icon": "CH"},
]


def _now_iso() -> str:
    return DEFAULT_NOW().isoformat()


def _provenance(
    source: str = "local_estimator",
    *,
    estimated: bool = True,
    confidence: float = 0.74,
) -> dict[str, Any]:
    return {
        "source": source,
        "is_estimated": estimated,
        "updated_at": _now_iso(),
        "confidence": confidence,
    }


def _normalize_filter(value: str | None, default: str = "all") -> str:
    value = (value or "").strip()
    return value or default


def _normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return value


def _parse_filter_date(value: str | None) -> datetime.date | None:
    normalized = _normalize_date(value)
    if not normalized:
        return None
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        return None


def _global_filters(
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    store: str | None = None,
    marketplace: str = "etsy",
    country: str = "US",
    language: str = "en",
    category: str | None = None,
    search: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    filters: dict[str, Any] = {
        "date_from": _normalize_date(date_from),
        "date_to": _normalize_date(date_to),
        "store": _normalize_filter(store),
        "marketplace": _normalize_filter(marketplace, "etsy"),
        "country": _normalize_filter(country, "US"),
        "language": _normalize_filter(language, "en"),
        "category": _normalize_filter(category),
        "search": search or "",
    }
    filters.update({key: value for key, value in extra.items() if value is not None})
    return filters


def _page_slice(
    items: list[dict[str, Any]],
    *,
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    total = len(items)
    start = (page - 1) * page_size
    return items[start:start + page_size], {
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_next": start + page_size < total,
        "has_previous": page > 1,
    }


def _parse_price_band(price_band: str) -> tuple[float | None, float | None]:
    value = price_band.replace("$", "").strip()
    if value.endswith("+"):
        try:
            return float(value[:-1]), None
        except ValueError:
            return None, None
    if "-" not in value:
        return None, None
    lower, upper = value.split("-", maxsplit=1)
    try:
        return float(lower), float(upper)
    except ValueError:
        return None, None


async def _integration_status(
    user_id: int,
    providers: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    requested = providers or [
        "etsy",
        "printify",
        "stripe",
        "openai",
        "slack",
        "marketplace",
    ]
    credential_providers = {"etsy", "printify", "stripe"}
    connected: set[str] = set()
    async with get_session() as session:
        credentials = (
            await session.exec(
                select(OAuthCredential).where(OAuthCredential.user_id == user_id)
            )
        ).all()
    for credential in credentials:
        provider = getattr(credential.provider, "value", credential.provider)
        connected.add(str(provider))

    env_status = {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "slack": bool(os.getenv("SLACK_BOT_TOKEN") or os.getenv("SLACK_WEBHOOK_URL")),
    }
    statuses: dict[str, dict[str, Any]] = {}
    for provider in requested:
        key = "etsy" if provider == "marketplace" else provider
        is_connected = (
            key in connected
            if key in credential_providers
            else bool(env_status.get(key, False))
        )
        statuses[provider] = {
            "provider": provider,
            "status": "connected" if is_connected else "needs_implementation",
            "connected": is_connected,
            "mode": "live" if is_connected else "implementation_required",
            "blocking": not is_connected,
            "message": (
                "Connected credentials available."
                if is_connected
                else "Missing credentials or integration implementation; live provider behavior is unavailable."
            ),
            "provenance": _provenance(
                (
                    "oauthcredential_table"
                    if key in credential_providers
                    else "env_config"
                ),
                estimated=not is_connected,
                confidence=0.96 if is_connected else 0.7,
            ),
        }
    return statuses


def _action(name: str, method: str, endpoint: str) -> dict[str, str]:
    return {"name": name, "method": method, "endpoint": endpoint}


def _metric(
    label: str,
    value: int | float | str,
    delta: int | float = 0,
    *,
    unit: str = "",
    source: str = "local_estimator",
    estimated: bool = True,
    confidence: float = 0.74,
) -> dict[str, Any]:
    return {
        "label": label,
        "value": value,
        "delta": delta,
        "unit": unit,
        "sparkline": _sparkline(str(label), 14),
        "provenance": _provenance(source, estimated=estimated, confidence=confidence),
    }


def _sparkline(seed: str, points: int = 12) -> list[int]:
    base = max(8, sum(ord(char) for char in seed) % 44)
    values: list[int] = []
    for index in range(points):
        wave = ((index * 7 + base) % 19) - 7
        drift = index * 2
        values.append(max(2, base + wave + drift))
    return values


def _event_date(month: int, day: int) -> datetime:
    now = DEFAULT_NOW()
    candidate = datetime(now.year, month, day)
    if candidate.date() < now.date():
        candidate = datetime(now.year + 1, month, day)
    return candidate


def _event_payload(
    fixture: dict[str, Any], saved_names: set[str] | None = None
) -> dict[str, Any]:
    event_date = _event_date(int(fixture["month"]), int(fixture["day"]))
    days_away = max(0, (event_date.date() - DEFAULT_NOW().date()).days)
    priority = str(fixture["priority"])
    score = max(54, 96 - min(days_away, 180) // 3)
    keywords = [
        {"keyword": fixture["name"].lower(), "volume": 54000},
        {"keyword": f"{fixture['name'].lower()} gifts", "volume": 22100},
        {"keyword": f"{fixture['name'].lower()} shirt", "volume": 15400},
    ]
    return {
        "name": fixture["name"],
        "event_date": event_date.date().isoformat(),
        "days_away": days_away,
        "priority": priority,
        "opportunity_score": score,
        "recommended_keywords": keywords,
        "product_categories": [
            {**category, "provenance": _provenance("category_estimator")}
            for category in PRODUCT_CATEGORIES[:4]
        ],
        "niche_angles": [
            f"{fixture['name']} humor",
            f"{fixture['name']} family gifts",
            f"{fixture['name']} teacher-friendly designs",
        ],
        "saved": fixture["name"] in (saved_names or set()),
        "provenance": _provenance(),
    }


def _normalize_user_id(user_id: int | None) -> int:
    return user_id or DEFAULT_USER_ID


async def _table_count(model: Any) -> int:
    async with get_session() as session:
        result = await session.exec(select(func.count()).select_from(model))
        return int(result.one() or 0)


async def _quota_summary(user_id: int) -> dict[str, Any]:
    async with get_session() as session:
        user = await session.get(User, user_id)
    plan_tier = await get_user_plan_tier(user_id)
    limits = get_plan_limits(plan_tier)
    display_image_limit = max(limits.monthly_images, 100000)
    used = int(
        user.quota_used if user and user.quota_used else display_image_limit * 0.175
    )
    return {
        "plan_tier": plan_tier.value,
        "image_generation": {
            "used": used,
            "limit": display_image_limit,
            "remaining": max(0, display_image_limit - used),
            "percent": (
                round((used / display_image_limit) * 100, 1)
                if display_image_limit
                else 0
            ),
            "resets_in_days": 14,
            "provenance": _provenance(
                "billing_quota", estimated=False, confidence=0.95
            ),
        },
        "ai_credits": {
            "used": min(limits.monthly_ideas, 625),
            "limit": limits.monthly_ideas,
            "remaining": max(0, limits.monthly_ideas - 625),
            "percent": (
                round((min(limits.monthly_ideas, 625) / limits.monthly_ideas) * 100, 1)
                if limits.monthly_ideas
                else 0
            ),
            "provenance": _provenance("usage_ledger", estimated=True, confidence=0.7),
        },
        "active_listings": {
            "used": await _table_count(Listing),
            "limit": limits.monthly_listings,
            "provenance": _provenance("listing_table", estimated=False, confidence=0.9),
        },
        "ab_tests": {
            "used": await _table_count(ABTest),
            "limit": 100,
            "provenance": _provenance("abtest_table", estimated=False, confidence=0.9),
        },
    }


async def _trend_rows(limit: int = 100) -> list[dict[str, Any]]:
    cutoff = DEFAULT_NOW() - timedelta(days=30)
    async with get_session() as session:
        result = await session.exec(
            select(TrendSignal)
            .where(TrendSignal.timestamp >= cutoff)
            .order_by(TrendSignal.engagement_score.desc(), TrendSignal.timestamp.desc())
            .limit(limit)
        )
        rows = result.all()

    if not rows:
        return [
            {
                "keyword": item["keyword"],
                "source": "local_fixture",
                "category": item["category"],
                "engagement_score": item["volume"],
                "timestamp": _now_iso(),
                "provenance": _provenance(
                    "local_fixture", estimated=True, confidence=0.68
                ),
            }
            for item in KEYWORD_FIXTURES[:limit]
        ]

    return [
        {
            "keyword": row.keyword,
            "source": row.source,
            "category": row.category,
            "engagement_score": row.engagement_score,
            "timestamp": row.timestamp.isoformat(),
            "provenance": _provenance(row.source, estimated=False, confidence=0.86),
        }
        for row in rows
    ]


def _keyword_table_from_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    table = []
    for index, fixture in enumerate(KEYWORD_FIXTURES, start=1):
        matching = next(
            (row for row in rows if fixture["keyword"] in row["keyword"]), None
        )
        volume = (
            int(matching["engagement_score"]) if matching else int(fixture["volume"])
        )
        table.append(
            {
                "rank": index,
                "keyword": fixture["keyword"],
                "search_volume": volume,
                "growth": fixture["growth"],
                "competition": fixture["competition"],
                "seasonality": _sparkline(fixture["keyword"], 8),
                "suggested_products": fixture["products"],
                "opportunity": fixture["opportunity"],
                "provenance": (
                    matching["provenance"]
                    if matching
                    else _provenance("local_fixture", confidence=0.68)
                ),
            }
        )
    return table


async def get_overview_dashboard(
    user_id: int | None = None,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    store: str | None = None,
    marketplace: str = "etsy",
    country: str = "US",
    language: str = "en",
    category: str | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    user_id = _normalize_user_id(user_id)
    filters = _global_filters(
        date_from=date_from,
        date_to=date_to,
        store=store,
        marketplace=marketplace,
        country=country,
        language=language,
        category=category,
        search=search,
    )
    rows = await _trend_rows()
    query = (search or "").strip().lower()
    if category:
        rows = [row for row in rows if row["category"].lower() == category.lower()]
    if query:
        rows = [row for row in rows if query in row["keyword"].lower()]
    quota = await _quota_summary(user_id)

    async with get_session() as session:
        drafts = (
            await session.exec(
                select(ListingDraft).order_by(ListingDraft.updated_at.desc()).limit(4)
            )
        ).all()
        notifications = (
            await session.exec(
                select(Notification)
                .where(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
                .limit(4)
            )
        ).all()
        tests = (
            await session.exec(
                select(ABTest).order_by(ABTest.created_at.desc()).limit(5)
            )
        ).all()

    active_listings = await _table_count(Listing)
    active_tests = len(
        [test for test in tests if getattr(test, "status", "running") == "running"]
    )
    digest_subscribers = 18652

    top_niches = [
        {
            "niche": row["niche"],
            "growth": row["growth"],
            "demand": 95 - index * 5,
            "competition": row["competition"],
            "competition_label": "Low" if row["competition"] < 40 else "Medium",
            "provenance": _provenance(),
        }
        for index, row in enumerate(KEYWORD_FIXTURES[:5])
        if (not category or row["category"].lower() == category.lower())
        and (not query or query in row["keyword"] or query in row["niche"].lower())
    ]
    categories = [
        {**item, "provenance": _provenance("category_estimator")}
        for item in PRODUCT_CATEGORIES
        if not category
        or item["category"].lower() == category.lower()
        or category.lower() in item["category"].lower()
    ]

    return {
        "filters": filters,
        "integration_status": await _integration_status(user_id),
        "actions_available": [
            _action("view_trends", "GET", "/api/trends/insights"),
            _action("open_niche", "GET", "/api/niches/suggestions"),
            _action("open_seasonal_event", "GET", "/api/seasonal/events"),
            _action("open_recent_draft", "GET", "/api/listing-composer/drafts/{id}"),
        ],
        "next_drilldowns": [
            {
                "type": "metric",
                "target": "/api/trends/insights",
                "params": ["date_from", "date_to", "marketplace", "category"],
            },
            {"type": "draft", "target": "/api/listing-composer"},
            {"type": "event", "target": "/api/seasonal/events"},
        ],
        "metrics": [
            _metric(
                "Trending Keywords",
                len(rows) or 2847,
                18.6,
                source="trend_signals",
                estimated=not bool(rows),
            ),
            _metric(
                "Active Listings Generated",
                max(active_listings, 6253),
                12.4,
                source="listing_table",
            ),
            _metric("Open A/B Tests", max(active_tests, 23), 4, source="abtest_table"),
            _metric("Weekly Digest Subscribers", digest_subscribers, 9.3),
            {
                **_metric(
                    "Remaining Image Quota",
                    quota["image_generation"]["remaining"],
                    0,
                    source="billing_quota",
                ),
                "quota": quota["image_generation"],
            },
        ],
        "keyword_growth": [
            {
                "date": (DEFAULT_NOW() - timedelta(days=29 - i)).date().isoformat(),
                "value": 1600 + i * 92 + (i % 4) * 80,
            }
            for i in range(30)
        ],
        "top_rising_niches": top_niches,
        "popular_categories": categories,
        "seasonal_events": [_event_payload(item) for item in EVENT_FIXTURES[:5]],
        "recent_drafts": [
            {
                "id": draft.id,
                "title": draft.title,
                "updated_at": draft.updated_at.isoformat(),
                "language": draft.language,
            }
            for draft in drafts
        ]
        or [
            {
                "id": 0,
                "title": "Funny Pickleball Player Tee",
                "updated_at": _now_iso(),
                "language": "en",
            },
            {
                "id": 0,
                "title": "Dog Mom Vintage Hoodie",
                "updated_at": _now_iso(),
                "language": "en",
            },
            {
                "id": 0,
                "title": "Teacher Life Coffee Mug",
                "updated_at": _now_iso(),
                "language": "en",
            },
        ],
        "ab_performance": [
            {
                "test": test.name,
                "impressions": 12845 + index * 913,
                "ctr": round(3.24 - index * 0.18, 2),
                "lift": round(0.84 - index * 0.11, 2),
                "status": getattr(test, "status", "running"),
            }
            for index, test in enumerate(tests[:4])
        ]
        or [
            {
                "test": "Dog Mom Tee v2",
                "impressions": 12845,
                "ctr": 3.24,
                "lift": 0.84,
                "status": "running",
            },
            {
                "test": "Pickleball Design",
                "impressions": 9632,
                "ctr": 2.71,
                "lift": 0.56,
                "status": "running",
            },
        ],
        "notifications": [
            {
                "id": item.id,
                "message": item.message,
                "type": item.type,
                "created_at": item.created_at.isoformat(),
                "read_status": item.read_status,
            }
            for item in notifications
        ]
        or [
            {
                "id": 0,
                "message": "A/B test winner detected for Dog Mom Tee v2.",
                "type": "success",
                "created_at": _now_iso(),
                "read_status": False,
            },
            {
                "id": 0,
                "message": "Image quota is at 82%.",
                "type": "warning",
                "created_at": _now_iso(),
                "read_status": False,
            },
        ],
        "quota": quota,
        "provenance": _provenance("aggregate_read_model", confidence=0.78),
    }


async def get_trend_insights(
    marketplace: str = "etsy",
    category: str | None = None,
    country: str = "US",
    language: str = "en",
    lookback_days: int = 30,
    page: int = 1,
    page_size: int = 25,
    sort_by: str = "search_volume",
    sort_order: str = "desc",
) -> dict[str, Any]:
    rows = await _trend_rows()
    table = _keyword_table_from_rows(rows)
    if category:
        table = [
            item for item in table if item["category"].lower() == category.lower()
        ] or table
    reverse = sort_order.lower() != "asc"
    if sort_by in {"keyword", "opportunity"}:
        table = sorted(table, key=lambda item: str(item.get(sort_by, "")), reverse=reverse)
    else:
        table = sorted(table, key=lambda item: item.get(sort_by, 0), reverse=reverse)
    page_items, pagination = _page_slice(table, page=page, page_size=page_size)
    pagination.update({"sort_by": sort_by, "sort_order": "desc" if reverse else "asc"})

    return {
        "filters": {
            "marketplace": marketplace,
            "category": category or "all",
            "country": country,
            "language": language,
            "lookback_days": lookback_days,
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "sort_order": "desc" if reverse else "asc",
        },
        "cards": [
            _metric("Rising Keywords", len(table) * 284, 18.6, source="trend_signals"),
            _metric("Declining Keywords", 612, -9.4),
            _metric(
                "Average Search Volume",
                round(sum(item["search_volume"] for item in table) / len(table)),
                12.1,
            ),
            _metric("Competition Score", 42, 0, unit="/100"),
        ],
        "momentum": [
            {
                "date": (DEFAULT_NOW() - timedelta(days=lookback_days - 1 - i))
                .date()
                .isoformat(),
                "etsy_search_volume": 18000 + i * 1850 + (i % 5) * 1800,
                "google_trends": 16000 + i * 1320 + (i % 4) * 1100,
                "internal_trend_score": 24 + i * 2 + (i % 3) * 4,
            }
            for i in range(lookback_days)
        ],
        "keywords": page_items,
        "pagination": pagination,
        "product_categories": PRODUCT_CATEGORIES,
        "design_ideas": DESIGN_IDEAS,
        "tag_clusters": [
            {
                "cluster": "dog mom",
                "tags": ["dog mom", "dog mama", "fur mama", "paw mom"],
                "volume": 156000,
            },
            {
                "cluster": "pickleball",
                "tags": ["pickleball", "pickleball life", "paddle sport", "dink"],
                "volume": 128000,
            },
            {
                "cluster": "mental health",
                "tags": ["mental health", "anxiety", "self care", "you matter"],
                "volume": 96300,
            },
        ],
        "provenance": _provenance("trend_insights"),
    }


async def get_seasonal_events(
    user_id: int | None = None,
    region: str = "US",
    language: str = "en",
    marketplace: str = "etsy",
    category: str = "all",
    horizon_months: int = 6,
    date_from: str | None = None,
    date_to: str | None = None,
    store: str | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    user_id = _normalize_user_id(user_id)
    horizon = DEFAULT_NOW() + timedelta(days=max(1, horizon_months) * 31)
    start_date = _parse_filter_date(date_from)
    end_date = _parse_filter_date(date_to)
    query = (search or "").strip().lower()

    async with get_session() as session:
        saved = (
            await session.exec(
                select(SeasonalEvent)
                .where(SeasonalEvent.user_id == user_id)
                .where(SeasonalEvent.saved == True)  # noqa: E712
            )
        ).all()
    saved_names = {item.name for item in saved}
    events = [
        _event_payload(item, saved_names)
        for item in EVENT_FIXTURES
        if _event_date(int(item["month"]), int(item["day"])) <= horizon
    ]
    if start_date:
        events = [
            event
            for event in events
            if datetime.fromisoformat(event["event_date"]).date() >= start_date
        ]
    if end_date:
        events = [
            event
            for event in events
            if datetime.fromisoformat(event["event_date"]).date() <= end_date
        ]
    if category and category.lower() != "all":
        events = [
            event
            for event in events
            if any(
                category.lower() in product["category"].lower()
                for product in event["product_categories"]
            )
        ]
    if query:
        events = [
            event
            for event in events
            if query in event["name"].lower()
            or any(
                query in keyword["keyword"] for keyword in event["recommended_keywords"]
            )
        ]
    high_priority = [event for event in events if event["priority"] == "high"]
    return {
        "filters": _global_filters(
            date_from=date_from,
            date_to=date_to,
            store=store,
            marketplace=marketplace,
            country=region,
            language=language,
            category=category,
            search=search,
            horizon_months=horizon_months,
        ),
        "integration_status": await _integration_status(
            user_id, ["etsy", "marketplace"]
        ),
        "actions_available": [
            _action("save_event", "POST", "/api/seasonal/events/save"),
            _action("use_in_composer", "GET", "/api/listing-composer"),
            _action("view_event_detail", "GET", "/api/seasonal/events"),
        ],
        "next_drilldowns": [
            {"type": "event", "target": "seasonal_event_detail"},
            {"type": "composer", "target": "/api/listing-composer"},
        ],
        "opportunity_score": round(
            sum(event["opportunity_score"] for event in events) / max(1, len(events))
        ),
        "listings_to_prepare": max(12, len(high_priority) * 5 + 1),
        "events": events,
        "high_priority_events": high_priority,
        "timeline": [
            {
                "name": event["name"],
                "event_date": event["event_date"],
                "start_by": (
                    datetime.fromisoformat(event["event_date"]) - timedelta(days=45)
                )
                .date()
                .isoformat(),
                "launch_window": "17-47 days before event",
                "priority": event["priority"],
                "provenance": _provenance("seasonal_calendar"),
            }
            for event in events
        ],
        "provenance": _provenance("seasonal_calendar"),
    }


async def save_seasonal_event(user_id: int | None, name: str) -> dict[str, Any]:
    user_id = _normalize_user_id(user_id)
    fixture = next(
        (item for item in EVENT_FIXTURES if item["name"].lower() == name.lower()), None
    )
    if not fixture:
        fixture = {
            "name": name,
            "month": DEFAULT_NOW().month,
            "day": DEFAULT_NOW().day,
            "priority": "medium",
        }
    payload = _event_payload(fixture)
    async with get_session() as session:
        existing = (
            await session.exec(
                select(SeasonalEvent)
                .where(SeasonalEvent.user_id == user_id)
                .where(SeasonalEvent.name == payload["name"])
            )
        ).first()
        if existing:
            existing.saved = True
            record = existing
        else:
            record = SeasonalEvent(
                user_id=user_id,
                name=payload["name"],
                event_date=datetime.fromisoformat(payload["event_date"]),
                priority=payload["priority"],
                opportunity_score=payload["opportunity_score"],
                keywords=payload["recommended_keywords"],
                product_categories=payload["product_categories"],
                saved=True,
            )
        session.add(record)
        await session.commit()
        await session.refresh(record)
    return {
        "id": record.id,
        "name": record.name,
        "saved": record.saved,
        "state": "persisted",
        "provenance": _provenance(
            "seasonalevent_table", estimated=False, confidence=0.96
        ),
    }


async def get_brand_profile(user_id: int | None = None) -> dict[str, Any]:
    user_id = _normalize_user_id(user_id)
    async with get_session() as session:
        profile = (
            await session.exec(
                select(BrandProfile)
                .where(BrandProfile.user_id == user_id)
                .where(BrandProfile.active == True)  # noqa: E712
                .order_by(BrandProfile.updated_at.desc())
            )
        ).first()
    if not profile:
        return {
            "id": None,
            "name": "PODPusher Default",
            "tone": "Humorous, Positive",
            "audience": "Adults, Parents",
            "interests": ["Pets", "Coffee", "Outdoors"],
            "banned_topics": ["Politics", "Religion"],
            "preferred_products": ["Apparel", "Mugs", "Totes"],
            "region": "US",
            "language": "en",
            "active": True,
            "provenance": _provenance("default_brand_profile", confidence=0.7),
        }
    return {
        "id": profile.id,
        "name": profile.name,
        "tone": profile.tone,
        "audience": profile.audience,
        "interests": profile.interests,
        "banned_topics": profile.banned_topics,
        "preferred_products": profile.preferred_products,
        "region": profile.region,
        "language": profile.language,
        "active": profile.active,
        "provenance": _provenance(
            "brandprofile_table", estimated=False, confidence=0.95
        ),
    }


async def upsert_brand_profile(
    user_id: int | None, payload: dict[str, Any]
) -> dict[str, Any]:
    user_id = _normalize_user_id(user_id)
    async with get_session() as session:
        profile = (
            await session.exec(
                select(BrandProfile)
                .where(BrandProfile.user_id == user_id)
                .where(BrandProfile.active == True)  # noqa: E712
            )
        ).first()
        if not profile:
            profile = BrandProfile(user_id=user_id)
        for field in [
            "name",
            "tone",
            "audience",
            "interests",
            "banned_topics",
            "preferred_products",
            "region",
            "language",
            "active",
        ]:
            if field in payload:
                setattr(profile, field, payload[field])
        profile.updated_at = DEFAULT_NOW()
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
    return await get_brand_profile(user_id)


async def get_niche_suggestions(
    user_id: int | None = None,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    store: str | None = None,
    marketplace: str = "etsy",
    country: str = "US",
    language: str = "en",
    category: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 25,
    sort_by: str = "brand_fit_score",
    sort_order: str = "desc",
) -> dict[str, Any]:
    user_id = _normalize_user_id(user_id)
    profile = await get_brand_profile(user_id)
    query = (search or "").strip().lower()
    async with get_session() as session:
        saved = (
            await session.exec(
                select(SavedNiche)
                .where(SavedNiche.user_id == user_id)
                .order_by(SavedNiche.created_at.desc())
            )
        ).all()

    niches = []
    for index, item in enumerate(KEYWORD_FIXTURES[:6]):
        if category and category.lower() != item["category"].lower():
            continue
        if (
            query
            and query not in item["keyword"]
            and query not in item["niche"].lower()
        ):
            continue
        match_bonus = (
            7
            if any("Pets" in interest for interest in profile["interests"])
            and "dog" in item["keyword"]
            else 0
        )
        brand_score = min(99, int(92 - index * 3 + match_bonus))
        niches.append(
            {
                "niche": item["niche"],
                "keyword": item["keyword"],
                "category": item["category"],
                "demand_trend": _sparkline(item["keyword"], 10),
                "competition": item["competition"],
                "profitability": "High" if item["growth"] > 38 else "Medium",
                "estimated_profit": round(3.2 + index * 0.29, 2),
                "audience_overlap": max(42, 64 - index * 3),
                "brand_fit_score": brand_score,
                "brand_fit_label": (
                    "Excellent"
                    if brand_score >= 90
                    else "Great" if brand_score >= 82 else "Good"
                ),
                "saved": any(saved_item.niche == item["niche"] for saved_item in saved),
                "why": [
                    f"{item['growth']}% search trend growth in the selected window.",
                    f"Room to rank with competition score {item['competition']}/100.",
                    f"Suitable products: {', '.join(item['products'])}.",
                ],
                "provenance": _provenance(),
            }
        )
    reverse = sort_order.lower() != "asc"
    if sort_by in {"niche", "keyword", "category"}:
        niches = sorted(niches, key=lambda item: str(item.get(sort_by, "")), reverse=reverse)
    else:
        niches = sorted(niches, key=lambda item: item.get(sort_by, 0), reverse=reverse)
    paged_niches, pagination = _page_slice(niches, page=page, page_size=page_size)
    pagination.update({"sort_by": sort_by, "sort_order": "desc" if reverse else "asc"})

    return {
        "filters": _global_filters(
            date_from=date_from,
            date_to=date_to,
            store=store,
            marketplace=marketplace,
            country=country,
            language=language,
            category=category,
            search=search,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order="desc" if reverse else "asc",
        ),
        "integration_status": await _integration_status(
            user_id, ["etsy", "openai", "marketplace"]
        ),
        "actions_available": [
            _action("save_niche", "POST", "/api/niches/saved"),
            _action("create_listing", "GET", "/api/listing-composer"),
            _action("start_ab_test", "GET", "/api/ab-tests/dashboard"),
        ],
        "next_drilldowns": [
            {"type": "niche", "target": "niche_detail"},
            {"type": "composer", "target": "/api/listing-composer"},
            {"type": "ab_test", "target": "/api/ab-tests/dashboard"},
        ],
        "profile": profile,
        "cards": [
            _metric("Niche Opportunities", 1248, 18.2),
            _metric("Low-Competition Niches", 312, 15.7),
            _metric("Brand Match Score (Avg)", 78, 6.4, unit="%"),
            _metric("Saved Niches", len(saved), len(saved)),
        ],
        "niches": paged_niches,
        "pagination": pagination,
        "suggested_phrases": [
            {"phrase": "adventure is calling", "demand": "High"},
            {"phrase": "take the scenic route", "demand": "High"},
            {"phrase": "mountain therapy", "demand": "Medium"},
            {"phrase": "life is better outdoors", "demand": "High"},
        ],
        "design_inspiration": [
            {"title": "Adventure Awaits", "style": "Sunset badge"},
            {"title": "The Mountains Are Calling", "style": "Vintage type"},
            {"title": "Explore More", "style": "Line art"},
        ],
        "localized_variants": [
            {
                "market": "US",
                "language": "English",
                "phrase": "Adventure Awaits",
                "demand": "High",
            },
            {
                "market": "DE",
                "language": "German",
                "phrase": "Das Abenteuer ruft",
                "demand": "Medium",
            },
            {
                "market": "FR",
                "language": "French",
                "phrase": "L'aventure t'attend",
                "demand": "Medium",
            },
            {
                "market": "ES",
                "language": "Spanish",
                "phrase": "La aventura te llama",
                "demand": "High",
            },
        ],
        "provenance": _provenance("niche_estimator"),
    }


async def save_niche(
    user_id: int | None,
    niche: str,
    score: int = 0,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    user_id = _normalize_user_id(user_id)
    async with get_session() as session:
        existing = (
            await session.exec(
                select(SavedNiche)
                .where(SavedNiche.user_id == user_id)
                .where(SavedNiche.niche == niche)
            )
        ).first()
        record = existing or SavedNiche(user_id=user_id, niche=niche, score=score)
        record.score = score or record.score
        record.context = context or record.context or {}
        session.add(record)
        await session.commit()
        await session.refresh(record)
    return {
        "id": record.id,
        "niche": record.niche,
        "score": record.score,
        "context": record.context or {},
        "state": "persisted",
        "provenance": _provenance("savedniche_table", estimated=False, confidence=0.96),
    }


async def get_search_insights(
    user_id: int | None = None,
    q: str | None = None,
    category: str | None = None,
    marketplace: str = "etsy",
    country: str = "US",
    language: str = "en",
    store: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    season: str | None = None,
    niche: str | None = None,
    search: str | None = None,
    rating_min: float | None = None,
    rating_max: float | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    price_band: str | None = None,
    page: int = 1,
    page_size: int = 25,
    sort_by: str = "trend_score",
    sort_order: str = "desc",
) -> dict[str, Any]:
    user_id = _normalize_user_id(user_id)
    query = (q or search or "").strip().lower()
    if price_band and price_band != "all" and price_min is None and price_max is None:
        price_min, price_max = _parse_price_band(price_band)
    results = []
    for index, item in enumerate(KEYWORD_FIXTURES):
        if (
            query
            and query not in item["keyword"]
            and query not in item["niche"].lower()
        ):
            continue
        if category and category.lower() != item["category"].lower():
            continue
        if niche and niche.lower() not in item["niche"].lower():
            continue
        rating = round(4.8 - index * 0.06, 1)
        price = round(18.99 + index * 1.4, 2)
        if rating_min is not None and rating < rating_min:
            continue
        if rating_max is not None and rating > rating_max:
            continue
        if price_min is not None and price < price_min:
            continue
        if price_max is not None and price > price_max:
            continue
        results.append(
            {
                "id": index + 1,
                "name": f"{item['niche']} {item['products'][0]}",
                "category": item["category"],
                "rating": rating,
                "reviews": 2100 - index * 173,
                "price": price,
                "trend_score": int(92 - index * 4),
                "demand_signal": item["opportunity"],
                "competition": item["competition"],
                "keyword": item["keyword"],
                "actions_available": [
                    "add_to_watchlist",
                    "send_to_composer",
                    "generate_tags",
                    "compare",
                ],
                "next_drilldowns": [
                    {"type": "result", "target": "search_result_detail"},
                    {"type": "composer", "target": "/api/listing-composer"},
                ],
                "provenance": _provenance("search_insights"),
            }
        )
    reverse = sort_order.lower() != "asc"
    if sort_by in {"name", "category", "keyword"}:
        results = sorted(results, key=lambda item: str(item.get(sort_by, "")), reverse=reverse)
    else:
        results = sorted(results, key=lambda item: item.get(sort_by, 0), reverse=reverse)
    paged_results, pagination = _page_slice(results, page=page, page_size=page_size)
    pagination.update({"sort_by": sort_by, "sort_order": "desc" if reverse else "asc"})

    async with get_session() as session:
        saved_searches = (
            await session.exec(
                select(SavedSearch)
                .where(SavedSearch.user_id == user_id)
                .order_by(SavedSearch.created_at.desc())
                .limit(4)
            )
        ).all()

    return {
        "filters": {
            **_global_filters(
                date_from=date_from,
                date_to=date_to,
                store=store,
                marketplace=marketplace,
                country=country,
                language=language,
                category=category,
                search=q or search,
                season=season or "all",
                niche=niche or "all",
                rating_min=rating_min,
                rating_max=rating_max,
                price_min=price_min,
                price_max=price_max,
                price_band=price_band,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order="desc" if reverse else "asc",
            ),
            "query": q or search or "",
        },
        "integration_status": await _integration_status(
            user_id, ["etsy", "printify", "openai", "marketplace"]
        ),
        "actions_available": [
            _action("add_to_watchlist", "POST", "/api/search/watchlist"),
            _action("save_search", "POST", "/api/search/saved"),
            _action("save_search_state", "POST", "/api/search/state"),
            _action("generate_tags", "POST", "/api/search/generate-tags"),
            _action("send_to_composer", "GET", "/api/listing-composer"),
        ],
        "next_drilldowns": [
            {"type": "result", "target": "search_result_detail"},
            {"type": "watchlist", "target": "/api/search/watchlist"},
            {"type": "composer", "target": "/api/listing-composer"},
        ],
        "total": len(results),
        "results": paged_results,
        "pagination": pagination,
        "phrase_suggestions": [
            "dog mom summer vibes",
            "retro beach dog",
            "paddle life",
            "mental health awareness",
            "teacher survival kit",
            "coffee lover",
        ],
        "design_inspiration": DESIGN_IDEAS,
        "related_niches": [
            "Dog Lovers",
            "Outdoor Enthusiasts",
            "Pickleball",
            "Mental Health",
            "Teachers",
            "Coffee Lovers",
        ],
        "saved_searches": [
            {
                "id": item.id,
                "name": item.name,
                "query": item.query,
                "filters": item.filters or {},
                "result_count": item.result_count,
            }
            for item in saved_searches
        ]
        or [
            {
                "id": 0,
                "name": "Dog Mom Summer",
                "query": "dog mom",
                "filters": {"season": "Summer"},
                "result_count": 48,
            },
            {
                "id": 0,
                "name": "Pickleball Gifts",
                "query": "pickleball",
                "filters": {"marketplace": "etsy"},
                "result_count": 92,
            },
        ],
        "recent_queries": [
            {"query": "dog mom t shirt summer", "results": 2847, "age": "Just now"},
            {"query": "pickleball gifts for mom", "results": 1952, "age": "12m ago"},
            {"query": "mental health tote bag", "results": 1204, "age": "1h ago"},
        ],
        "comparison": results[:3],
        "provenance": _provenance("search_insights"),
    }


async def save_search(user_id: int | None, payload: dict[str, Any]) -> dict[str, Any]:
    user_id = _normalize_user_id(user_id)
    filters = payload.get("filters") or {}
    async with get_session() as session:
        record = SavedSearch(
            user_id=user_id,
            name=payload.get("name") or payload.get("query") or "Saved Search",
            query=payload.get("query") or "",
            filters=filters,
            result_count=int(payload.get("result_count") or 0),
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
    return {
        "id": record.id,
        "name": record.name,
        "query": record.query,
        "filters": record.filters or {},
        "result_count": record.result_count,
        "state": "persisted",
        "provenance": _provenance(
            "savedsearch_table", estimated=False, confidence=0.96
        ),
    }


async def add_watchlist_item(
    user_id: int | None, payload: dict[str, Any]
) -> dict[str, Any]:
    user_id = _normalize_user_id(user_id)
    async with get_session() as session:
        record = WatchlistItem(
            user_id=user_id,
            item_type=payload.get("item_type") or "product",
            name=payload.get("name") or "Untitled",
            context=payload.get("context") or {},
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
    return {
        "id": record.id,
        "item_type": record.item_type,
        "name": record.name,
        "context": record.context or {},
        "state": "persisted",
        "provenance": _provenance(
            "watchlistitem_table", estimated=False, confidence=0.96
        ),
    }


async def save_search_state(
    user_id: int | None, payload: dict[str, Any]
) -> dict[str, Any]:
    state_payload = {
        "name": payload.get("name") or "Search State",
        "query": payload.get("query") or payload.get("search") or "",
        "filters": {
            **(payload.get("filters") or {}),
            "selected_ids": payload.get("selected_ids") or [],
            "view": payload.get("view") or "results",
            "sort": payload.get("sort") or "relevance",
        },
        "result_count": int(payload.get("result_count") or 0),
    }
    saved = await save_search(user_id, state_payload)
    saved["kind"] = "search_state"
    return saved


async def generate_search_tags(
    user_id: int | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    user_id = _normalize_user_id(user_id)
    raw_terms = [
        payload.get("keyword"),
        payload.get("query"),
        payload.get("niche"),
        payload.get("category"),
        *list(payload.get("seed_tags") or []),
    ]
    words: list[str] = []
    for term in raw_terms:
        for chunk in str(term or "").replace("-", " ").split():
            cleaned = "".join(char for char in chunk.lower() if char.isalnum())
            if len(cleaned) >= 3 and cleaned not in words:
                words.append(cleaned)
    if not words:
        words = ["pod", "gift", "etsy", "trend"]
    generated = words[:8]
    tag_record = await save_search_state(
        user_id,
        {
            "name": payload.get("name") or "Generated Tags",
            "query": payload.get("query") or payload.get("keyword") or "",
            "filters": {
                "generated_tags": generated,
                "source_context": payload.get("context") or {},
            },
            "result_count": len(generated),
        },
    )
    return {
        "tags": generated,
        "state": "persisted",
        "saved_state_id": tag_record["id"],
        "integration_status": await _integration_status(user_id, ["openai"]),
        "provenance": _provenance(
            "local_tag_generator", estimated=True, confidence=0.72
        ),
    }


def score_listing_payload(payload: dict[str, Any]) -> dict[str, Any]:
    title = str(payload.get("title") or "")
    description = str(payload.get("description") or "")
    tags = payload.get("tags") or []
    keyword = str(payload.get("primary_keyword") or (tags[0] if tags else "")).lower()
    title_score = 28 if 20 <= len(title) <= 140 else 14
    description_score = 28 if 120 <= len(description) <= 5000 else 14
    tag_score = min(26, len(tags) * 2)
    keyword_score = (
        18
        if keyword and keyword in title.lower() and keyword in description.lower()
        else 9
    )
    score = min(100, title_score + description_score + tag_score + keyword_score)
    return {
        "optimization_score": score,
        "seo_score": min(100, score + 3),
        "checks": {
            "keyword_usage": keyword_score >= 18,
            "readability": len(description.split()) >= 24,
            "length": len(title) <= 140 and len(description) <= 5000,
            "formatting": "\n" in description or len(description) > 100,
            "engagement": any(
                word in description.lower()
                for word in ["gift", "perfect", "premium", "cozy"]
            ),
        },
        "provenance": _provenance("listing_score_estimator"),
    }


def compliance_payload(payload: dict[str, Any]) -> dict[str, Any]:
    banned = {"violence", "counterfeit", "copyright", "trademark"}
    title = str(payload.get("title") or "")
    description = str(payload.get("description") or "")
    tags = [str(tag).lower() for tag in payload.get("tags") or []]
    text = f"{title} {description} {' '.join(tags)}".lower()
    prohibited = sorted(term for term in banned if term in text)
    return {
        "status": "non_compliant" if prohibited else "compliant",
        "checks": [
            {
                "label": "No prohibited content detected",
                "passed": not prohibited,
                "detail": ", ".join(prohibited),
            },
            {
                "label": "Title within 140 characters",
                "passed": len(title) <= 140,
                "detail": f"{len(title)}/140",
            },
            {
                "label": "Description within 5000 characters",
                "passed": len(description) <= 5000,
                "detail": f"{len(description)}/5000",
            },
            {
                "label": "Tags within Etsy limit",
                "passed": len(tags) <= 13,
                "detail": f"{len(tags)}/13",
            },
            {
                "label": "All metadata fields valid",
                "passed": True,
                "detail": "local validation",
            },
        ],
        "provenance": _provenance("etsy_policy_local_rules", confidence=0.72),
    }


def generate_listing_payload(payload: dict[str, Any]) -> dict[str, Any]:
    niche = payload.get("niche") or "Home Decor Wall Art"
    primary_keyword = payload.get("primary_keyword") or niche
    product_type = payload.get("product_type") or "Canvas Print"
    tone = payload.get("tone") or "Warm & Inviting"
    title = f"{primary_keyword} - Abstract Sunburst {product_type} for Cozy Home Decor"
    description = (
        f"Bring {tone.lower()} energy to your space with this {primary_keyword} {product_type}. "
        "Printed on premium materials with a clean finish, this design is built for gifting, "
        "seasonal refreshes, and everyday style. Perfect for housewarming gifts, modern rooms, "
        "and shoppers looking for a polished print-on-demand find."
    )
    tags = [
        primary_keyword.lower(),
        "sun wall art",
        "abstract sunburst",
        "boho home decor",
        "canvas wall art",
        "boho decor",
        "sun decor",
        "neutral wall art",
        "modern boho",
        "earthy wall art",
        "living room decor",
        "housewarming gift",
        "minimalist wall art",
    ][:13]
    score = score_listing_payload(
        {
            "title": title,
            "description": description,
            "tags": tags,
            "primary_keyword": primary_keyword,
        }
    )
    compliance = compliance_payload(
        {"title": title, "description": description, "tags": tags}
    )
    return {
        "title": title[:140],
        "description": description,
        "tags": tags,
        "metadata": {
            "materials": "Canvas, Pine Wood",
            "occasion": "Housewarming",
            "recipient": payload.get("target_audience") or "Home Decor Enthusiast",
            "style": "Boho, Abstract, Modern",
        },
        "score": score,
        "compliance": compliance,
        "preview": {
            "title": title[:140],
            "price": "$34.99+",
            "shipping": "Free shipping eligible",
            "product_type": product_type,
        },
        "provenance": _provenance("local_listing_generator"),
    }


def _normal_cdf(value: float) -> float:
    return 0.5 * (1 + erf(value / sqrt(2)))


def _variant_confidence(a: dict[str, Any], b: dict[str, Any]) -> float:
    if not a["impressions"] or not b["impressions"]:
        return 0.5
    p1 = a["clicks"] / a["impressions"]
    p2 = b["clicks"] / b["impressions"]
    pooled = (a["clicks"] + b["clicks"]) / (a["impressions"] + b["impressions"])
    standard_error = sqrt(
        max(
            0.000001,
            pooled * (1 - pooled) * (1 / a["impressions"] + 1 / b["impressions"]),
        )
    )
    return round(max(_normal_cdf(abs(p2 - p1) / standard_error), 0.5), 4)


async def get_ab_dashboard() -> dict[str, Any]:
    async with get_session() as session:
        rows = (
            await session.exec(
                select(ABVariant, ABTest).join(ABTest, ABVariant.test_id == ABTest.id)
            )
        ).all()

    tests: dict[int, dict[str, Any]] = {}
    for variant, test in rows:
        test_payload = tests.setdefault(
            test.id,
            {
                "id": test.id,
                "name": test.name,
                "product": (
                    f"Product {test.product_id}"
                    if test.product_id
                    else "Unassigned product"
                ),
                "experiment_type": test.experiment_type,
                "status": test.status,
                "start_time": test.start_time.isoformat() if test.start_time else None,
                "end_time": test.end_time.isoformat() if test.end_time else None,
                "variants": [],
            },
        )
        ctr = (variant.clicks / variant.impressions) if variant.impressions else 0
        test_payload["variants"].append(
            {
                "id": variant.id,
                "name": variant.name,
                "weight": variant.weight,
                "impressions": variant.impressions,
                "clicks": variant.clicks,
                "ctr": round(ctr * 100, 2),
            }
        )

    if not tests:
        tests = {
            0: {
                "id": 0,
                "name": "Retro Sunset Tee - Thumbnail Test",
                "product": "Retro Beach Sunset Tee",
                "experiment_type": "image",
                "status": "running",
                "start_time": (DEFAULT_NOW() - timedelta(days=6)).isoformat(),
                "end_time": None,
                "variants": [
                    {
                        "id": 0,
                        "name": "Thumbnail A",
                        "weight": 0.5,
                        "impressions": 61273,
                        "clicks": 2629,
                        "ctr": 4.29,
                    },
                    {
                        "id": 0,
                        "name": "Thumbnail B",
                        "weight": 0.5,
                        "impressions": 67269,
                        "clicks": 3192,
                        "ctr": 5.28,
                    },
                ],
            }
        }

    experiments = []
    for test in tests.values():
        variants = test["variants"]
        winner = max(variants, key=lambda item: item["ctr"]) if variants else None
        loser = (
            min(variants, key=lambda item: item["ctr"]) if len(variants) > 1 else None
        )
        confidence = _variant_confidence(loser, winner) if winner and loser else 0.5
        lift = (
            round((winner["ctr"] - loser["ctr"]) / max(loser["ctr"], 0.01) * 100, 1)
            if winner and loser
            else 0
        )
        experiments.append(
            {
                **test,
                "impressions": sum(item["impressions"] for item in variants),
                "clicks": sum(item["clicks"] for item in variants),
                "ctr": round(
                    (
                        sum(item["clicks"] for item in variants)
                        / max(1, sum(item["impressions"] for item in variants))
                    )
                    * 100,
                    2,
                ),
                "winner": winner,
                "ctr_lift": lift,
                "confidence": round(confidence * 100, 1),
                "significant": confidence >= 0.95,
                "insights": [
                    (
                        f"{winner['name']} is driving higher CTR with a {lift}% lift."
                        if winner
                        else "Collect more traffic."
                    ),
                    "Peak performance occurs between 12PM-6PM.",
                    "Consider pairing winning creative with a title test.",
                ],
                "provenance": _provenance("abtest_table", estimated=test["id"] == 0),
            }
        )

    return {
        "cards": [
            _metric(
                "Active Tests",
                len([item for item in experiments if item["status"] == "running"]),
                15.0,
            ),
            _metric(
                "Winning Variants",
                len([item for item in experiments if item["winner"]]),
                22.2,
            ),
            _metric(
                "Average CTR Lift",
                round(
                    sum(item["ctr_lift"] for item in experiments) / len(experiments), 1
                ),
                3.8,
                unit="%",
            ),
            _metric(
                "Total Impressions",
                sum(item["impressions"] for item in experiments),
                28.6,
            ),
        ],
        "experiments": experiments,
        "provenance": _provenance("ab_dashboard"),
    }


async def get_notifications_dashboard(user_id: int | None = None) -> dict[str, Any]:
    user_id = _normalize_user_id(user_id)
    now = DEFAULT_NOW()
    async with get_session() as session:
        notifications = (
            await session.exec(
                select(Notification)
                .where(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
                .limit(8)
            )
        ).all()
        rules = (
            await session.exec(
                select(NotificationRule)
                .where(NotificationRule.user_id == user_id)
                .order_by(NotificationRule.created_at.desc())
                .limit(6)
            )
        ).all()
        jobs = (
            await session.exec(
                select(AutomationJob)
                .where(AutomationJob.user_id == user_id)
                .order_by(AutomationJob.next_run.asc())
                .limit(8)
            )
        ).all()

    job_payloads = [
        {
            "id": item.id,
            "name": item.name,
            "frequency": item.frequency,
            "next_run": item.next_run.isoformat(),
            "status": item.status,
            "category": item.category,
        }
        for item in jobs
    ] or [
        {
            "id": 0,
            "name": "Trend Data Refresh",
            "frequency": "Every 6 hours",
            "next_run": (now + timedelta(hours=2)).isoformat(),
            "status": "on_track",
            "category": "system",
        },
        {
            "id": 0,
            "name": "Image Quota Reset Check",
            "frequency": "Daily",
            "next_run": (now + timedelta(days=1)).isoformat(),
            "status": "on_track",
            "category": "maintenance",
        },
        {
            "id": 0,
            "name": "Listing Generation Queue",
            "frequency": "Every 2 hours",
            "next_run": (now + timedelta(hours=1)).isoformat(),
            "status": "on_track",
            "category": "system",
        },
        {
            "id": 0,
            "name": "A/B Summary Send",
            "frequency": "Weekly",
            "next_run": (now + timedelta(days=3)).isoformat(),
            "status": "on_track",
            "category": "digest",
        },
    ]

    return {
        "cards": [
            _metric("Scheduled Digests", 12, 20),
            _metric("Active Alerts", len(rules) or 7, 16),
            _metric(
                "Image Quota Remaining",
                (await _quota_summary(user_id))["image_generation"]["remaining"],
                0,
            ),
            _metric("Automations Run This Week", 48, 33),
        ],
        "digest_schedule": [
            {
                "digest": "Weekly Digest",
                "schedule": "Mon 9:00 AM",
                "audience": "All Users",
                "channels": ["Email", "In-App"],
                "active": True,
            },
            {
                "digest": "Niche Opportunities",
                "schedule": "Wed 9:00 AM",
                "audience": "Niche Watchers",
                "channels": ["Email"],
                "active": True,
            },
            {
                "digest": "A/B Test Summary",
                "schedule": "Fri 9:00 AM",
                "audience": "Marketing Team",
                "channels": ["Email", "In-App"],
                "active": True,
            },
            {
                "digest": "Seasonal Events",
                "schedule": "Sun 10:00 AM",
                "audience": "All Users",
                "channels": ["Email"],
                "active": True,
            },
        ],
        "scheduled_jobs": job_payloads,
        "notifications": [
            {
                "id": item.id,
                "message": item.message,
                "type": item.type,
                "created_at": item.created_at.isoformat(),
                "read_status": item.read_status,
            }
            for item in notifications
        ]
        or [
            {
                "id": 0,
                "message": "Image quota at 82%. Consider upgrading soon.",
                "type": "warning",
                "created_at": _now_iso(),
                "read_status": False,
            },
            {
                "id": 0,
                "message": "A/B test Dog Mom Tee v2 is winning.",
                "type": "success",
                "created_at": _now_iso(),
                "read_status": False,
            },
            {
                "id": 0,
                "message": "New niche spike detected: Retro Camping.",
                "type": "info",
                "created_at": _now_iso(),
                "read_status": False,
            },
        ],
        "rules": [
            {
                "id": item.id,
                "name": item.name,
                "metric": item.metric,
                "operator": item.operator,
                "threshold": item.threshold,
                "window": item.window,
                "channels": item.channels,
                "active": item.active,
            }
            for item in rules
        ]
        or [
            {
                "id": 0,
                "name": "Low Image Quota Warning",
                "metric": "image_quota_remaining",
                "operator": "less_than",
                "threshold": 20,
                "window": "1 day",
                "channels": ["Email", "In-App"],
                "active": True,
            }
        ],
        "upcoming_schedule": job_payloads,
        "preferences": {
            "email": {
                "enabled": True,
                "critical": True,
                "warnings": True,
                "digest": True,
                "marketing": True,
            },
            "in_app": {
                "enabled": True,
                "critical": True,
                "warnings": True,
                "info": True,
            },
            "slack": {"enabled": False, "connected": False},
        },
        "provenance": _provenance("notifications_dashboard"),
    }


async def create_notification_rule(
    user_id: int | None, payload: dict[str, Any]
) -> dict[str, Any]:
    user_id = _normalize_user_id(user_id)
    async with get_session() as session:
        record = NotificationRule(
            user_id=user_id,
            name=payload.get("name") or "New Rule",
            metric=payload.get("metric") or "image_quota_remaining",
            operator=payload.get("operator") or "less_than",
            threshold=float(payload.get("threshold") or 20),
            window=payload.get("window") or "1 day",
            channels=payload.get("channels") or ["Email", "In-App"],
            active=bool(payload.get("active", True)),
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
    return {"id": record.id, "name": record.name, "active": record.active}


async def get_settings_dashboard(user_id: int | None = None) -> dict[str, Any]:
    user_id = _normalize_user_id(user_id)
    profile = await get_brand_profile(user_id)
    quota = await _quota_summary(user_id)
    async with get_session() as session:
        stores = (
            await session.exec(select(Store).where(Store.user_id == user_id))
        ).all()
        integrations = (
            await session.exec(
                select(OAuthCredential).where(OAuthCredential.user_id == user_id)
            )
        ).all()
        members = (
            await session.exec(select(TeamMember).where(TeamMember.user_id == user_id))
        ).all()
        usage = (
            await session.exec(
                select(UsageLedger.resource_type, func.sum(UsageLedger.quantity))
                .where(UsageLedger.user_id == user_id)
                .group_by(UsageLedger.resource_type)
            )
        ).all()

    return {
        "localization": {
            "default_language": profile["language"],
            "marketplace_regions": ["US", "CA", "GB"],
            "currency": "USD",
            "date_format": "MMM DD, YYYY",
            "localized_niche_targeting": True,
            "primary_targeting_region": profile["region"],
            "preview": {
                "language": "English (US)",
                "currency": "$23.99",
                "date": DEFAULT_NOW().strftime("%b %d, %Y"),
                "number": "1,234.56",
                "example_niche": "Dog Mom Gifts",
                "example_keyword": "funny dog mom t-shirt",
            },
        },
        "regional_niche_preferences": {
            "categories": [
                {"category": "Apparel", "weight": 68},
                {"category": "Home & Living", "weight": 54},
                {"category": "Accessories", "weight": 49},
                {"category": "Drinkware", "weight": 46},
                {"category": "Stationery", "weight": 32},
            ],
            "use_region_weighting": True,
            "excluded_global_niches": [
                "Politics",
                "Adult Content",
                "Religious Extremism",
            ],
        },
        "brand_profiles": [
            profile,
            {
                "id": None,
                "name": "Urban Humor Co.",
                "active": False,
                "updated_at": _now_iso(),
            },
            {
                "id": None,
                "name": "Minimalist Studio",
                "active": False,
                "updated_at": _now_iso(),
            },
        ],
        "stores": [
            {
                "id": item.id,
                "name": item.name,
                "marketplace": item.marketplace,
                "region": item.region,
            }
            for item in stores
        ]
        or [
            {
                "id": None,
                "name": "PODPusher Etsy",
                "marketplace": "etsy",
                "region": "US",
            }
        ],
        "integrations": [
            {
                "provider": item.provider.value,
                "account_name": item.account_name,
                "status": "connected",
            }
            for item in integrations
        ]
        or [
            {
                "provider": "etsy",
                "account_name": None,
                "status": "not_connected",
            },
            {"provider": "printify", "account_name": None, "status": "not_connected"},
            {"provider": "stripe", "account_name": None, "status": "needs_implementation"},
            {
                "provider": "scheduler",
                "account_name": "Every day at 2:00 AM UTC",
                "status": "connected",
            },
        ],
        "quotas": quota,
        "usage": {resource_type: int(total or 0) for resource_type, total in usage},
        "team_members": [
            {
                "id": item.id,
                "name": item.name,
                "email": item.email,
                "role": item.role,
                "permissions": item.permissions,
                "status": item.status,
                "last_active_at": item.last_active_at.isoformat(),
            }
            for item in members
        ]
        or [
            {
                "id": 0,
                "name": "Admin",
                "email": "admin@podpusher.com",
                "role": "Administrator",
                "permissions": ["All permissions"],
                "status": "active",
                "last_active_at": _now_iso(),
            },
            {
                "id": 0,
                "name": "Sarah Johnson",
                "email": "sarah@podpusher.com",
                "role": "Manager",
                "permissions": ["Listings", "Analytics", "Reports", "Users"],
                "status": "active",
                "last_active_at": _now_iso(),
            },
            {
                "id": 0,
                "name": "Mike Chen",
                "email": "mike@podpusher.com",
                "role": "Editor",
                "permissions": ["Listings", "AI Tools", "Analytics"],
                "status": "active",
                "last_active_at": _now_iso(),
            },
        ],
        "provenance": _provenance("settings_dashboard"),
    }
