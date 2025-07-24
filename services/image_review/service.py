from typing import List, Optional
from sqlmodel import select

from ..models import Product
from ..common.database import get_session


async def list_reviews() -> List[Product]:
    async with get_session() as session:
        result = await session.exec(select(Product))
        return result.all()


async def update_review(
    product_id: int,
    rating: Optional[int] = None,
    tags: Optional[List[str]] = None,
    flagged: Optional[bool] = None,
) -> Product | None:
    async with get_session() as session:
        product = await session.get(Product, product_id)
        if not product:
            return None
        if rating is not None:
            product.rating = rating
        if tags is not None:
            product.tags = ",".join(tags)
        if flagged is not None:
            product.flagged = flagged
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product
