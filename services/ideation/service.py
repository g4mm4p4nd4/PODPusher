from typing import List, Dict, Union
import asyncio
import os
from datetime import datetime
from ..models import Idea, Trend
from ..common.database import get_session
from ..trend_scraper.events import EVENTS
from packages.integrations import openai

# Simplified historical sales and search frequency data for tags
SALES_DATA: Dict[str, int] = {
    "t-shirt": 100,
    "mug": 80,
    "cat": 60,
    "dog": 50,
}

SEARCH_DATA: Dict[str, int] = {
    "cat": 120,
    "dog": 90,
    "mug": 40,
    "t-shirt": 30,
}


TrendInput = Union[str, Dict]


async def generate_ideas(trends: List[TrendInput]) -> List[Dict]:
    """Generate product ideas for the supplied trend signals."""

    normalized: List[Dict] = []
    for t in trends:
        if isinstance(t, dict):
            normalized.append(
                {
                    "id": t.get("id"),
                    "term": t.get("term") or t.get("keyword"),
                    "category": (t.get("category") or "general").lower(),
                }
            )
        else:
            normalized.append({"id": None, "term": t, "category": "general"})

    month = datetime.utcnow().strftime("%B").lower()
    events = EVENTS.get(month, [])
    prompt_events = ", ".join(events)
    prompts = [
        (
            f"Generate a product idea for the {item['category']} niche around '{item['term']}'. "
            f"Consider upcoming {prompt_events}"
        )
        for item in normalized
    ]

    try:
        ideas_text = await asyncio.gather(*[openai.generate_brief(prompt) for prompt in prompts])
    except Exception:
        fallback_products = ["t-shirt", "mug", "sticker", "tote bag"]
        ideas_text = []
        for idx, item in enumerate(normalized):
            product = fallback_products[idx % len(fallback_products)]
            ideas_text.append(f"{item['term']} {product}")

    ideas: List[Dict] = []
    async with get_session() as session:
        for item, text in zip(normalized, ideas_text):
            trend_id = item.get("id")
            if trend_id is None:
                trend = Trend(term=item['term'], category=item['category'])
                session.add(trend)
                await session.commit()
                await session.refresh(trend)
                trend_id = trend.id
            idea = Idea(trend_id=trend_id, description=text)
            session.add(idea)
            await session.commit()
            await session.refresh(idea)
            ideas.append(
                {
                    "id": idea.id,
                    "trend_id": trend_id,
                    "description": idea.description,
                    "term": item['term'],
                    "category": item['category'],
                }
            )
    return ideas


async def suggest_tags(title: str, description: str) -> List[str]:
    """Return ranked tag suggestions based on sales and search history."""
    text = f"{title} {description}".strip()
    raw: List[str] = []
    if openai.API_KEY and not openai.USE_STUB:
        try:
            raw = await openai.suggest_tags(text)
        except Exception:
            raw = []
    if not raw:
        words = [w.strip(".,!?:;\"'()[]{}").lower() for w in text.split()]
        stop = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "of",
            "in",
            "with",
            "to",
            "for",
            "on",
            "at",
            "by",
        }
        for w in words:
            if w and w not in stop:
                raw.append(w)
    seen = []
    for tag in raw:
        if tag not in seen:
            seen.append(tag)
    scored = sorted(
        seen,
        key=lambda t: SALES_DATA.get(t, 0) + SEARCH_DATA.get(t, 0),
        reverse=True,
    )
    return scored[:13]
