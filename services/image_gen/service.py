from typing import List, Dict
import os
from ..models import Product
from ..common.database import get_session


async def generate_images(ideas: List[str]) -> List[Dict]:
    if os.getenv("OPENAI_API_KEY"):
        try:
            import openai

            responses = [
                openai.Image.create(prompt=idea, n=1, size="512x512") for idea in ideas
            ]
            urls = [r["data"][0]["url"] for r in responses]
        except Exception:
            urls = ["http://example.com/image.png" for _ in ideas]
    else:
        urls = ["http://example.com/image.png" for _ in ideas]

    products = []
    async with get_session() as session:
        for idea, url in zip(ideas, urls):
            product = Product(idea_id=0, image_url=url)
            session.add(product)
            await session.commit()
            await session.refresh(product)
            products.append({"image_url": product.image_url})
    return products
