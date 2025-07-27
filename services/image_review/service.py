from typing import List, Optional
from sqlmodel import select

from ..models import Product
from ..common.database import get_session


async def list_products() -> List[dict]:
    async with get_session() as session:
        result = await session.exec(select(Product))
        products = result.all()
        return [
            {
                "id": p.id,
                "name": f"Product {p.id}",
                "image_url": p.image_url,
                "rating": p.rating,
                "tags": p.tags or [],
                "flagged": p.flagged,
            }
            for p in products
        ]


async def update_product(
    product_id: int,
    rating: Optional[int] = None,
    tags: Optional[List[str]] = None,
    flagged: Optional[bool] = None,
) -> Optional[dict]:
    async with get_session() as session:
        product = await session.get(Product, product_id)
        if not product:
            return None
        if rating is not None:
            product.rating = rating
        if tags is not None:
            product.tags = tags
        if flagged is not None:
            product.flagged = flagged
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return {
            "id": product.id,
            "name": f"Product {product.id}",
            "image_url": product.image_url,
            "rating": product.rating,
            "tags": product.tags or [],
            "flagged": product.flagged,
        }
