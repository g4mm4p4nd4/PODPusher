from typing import List, Dict, Union
import os
from datetime import datetime
from ..models import Idea
from ..common.database import get_session
from ..trend_scraper.events import EVENTS


TrendInput = Union[str, Dict]


async def generate_ideas(trends: List[TrendInput]) -> List[Dict]:
    formatted = []
    for t in trends:
        if isinstance(t, dict):
            term = t.get("term")
            category = t.get("category", "general")
        else:
            term = t
            category = "general"
        formatted.append((term, category))

    key = os.getenv("OPENAI_API_KEY")
    month = datetime.utcnow().strftime("%B").lower()
    events = EVENTS.get(month, [])
    prompt_events = ", ".join(events)
    prompts = [
        (
            f"Generate a product idea for the {cat} niche around '{term}'. "
            f"Consider upcoming {prompt_events}"
        )
        for term, cat in formatted
    ]

    if key:
        try:
            import openai

            responses = [
                openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": p}],
                )
                for p in prompts
            ]
            ideas_text = [r.choices[0].message.content for r in responses]
        except Exception:
            ideas_text = prompts
    else:
        product_types = ["t-shirt", "mug", "sticker", "tote bag"]
        ideas_text = []
        for term, _cat in formatted:
            for ptype in product_types[:2]:
                ideas_text.append(f"{term} {ptype}")

    ideas = []
    async with get_session() as session:
        for (term, cat), text in zip(formatted, ideas_text):
            idea = Idea(trend_id=0, description=text)  # stub trend_id
            session.add(idea)
            await session.commit()
            await session.refresh(idea)
            ideas.append(
                {"description": idea.description, "term": term, "category": cat}
            )
    return ideas


async def suggest_tags(description: str) -> List[str]:
    key = os.getenv("OPENAI_API_KEY")
    if key:
        try:
            import openai

            resp = await openai.ChatCompletion.acreate(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Suggest Etsy listing tags as a JSON array for: "
                            f"{description}"
                        ),
                    }
                ],
            )
            import json

            tags = json.loads(resp.choices[0].message.content)
            if isinstance(tags, list):
                return [str(t) for t in tags]
        except Exception:
            pass
    return description.lower().split()[:5]
