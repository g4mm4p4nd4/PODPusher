from typing import List, Dict
import os
from ..models import Idea
from ..common.database import get_session


async def generate_ideas(trends: List[str]) -> List[Dict]:
    if os.getenv("OPENAI_API_KEY"):
        try:
            import openai

            responses = [
                openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": f"Idea for {t}"}],
                )
                for t in trends
            ]
            ideas_text = [r.choices[0].message.content for r in responses]
        except Exception:
            ideas_text = [f"idea about {t}" for t in trends]
    else:
        ideas_text = [f"idea about {t}" for t in trends]

    ideas = []
    async with get_session() as session:
        for trend, text in zip(trends, ideas_text):
            idea = Idea(trend_id=0, description=text)  # stub trend_id
            session.add(idea)
            await session.commit()
            await session.refresh(idea)
            ideas.append({"description": idea.description})
    return ideas
