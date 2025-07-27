from typing import List, Optional
from sqlmodel import select

from ..models import Product, Idea, Trend
from ..common.database import get_session


async def search_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    rating_min: Optional[int] = None,
    page: int = 1,
    page_size: int = 10,
) -> List[dict]:
    """Filter products by keyword, category, tag and rating."""
    async with get_session() as session:
        stmt = (
            select(Product, Idea, Trend)
            .join(Idea, Product.idea_id == Idea.id)
            .join(Trend, Idea.trend_id == Trend.id)
        )
        if rating_min is not None:
            stmt = stmt.where(Product.rating >= rating_min)
        result = await session.exec(stmt)
        rows = result.all()

    items: List[dict] = []
    for product, idea, trend in rows:
        if q:
            q_lower = q.lower()
            if q_lower not in (idea.description or "").lower() and q_lower not in (
                trend.term or ""
            ).lower():
                continue
        if category and trend.category != category.lower():
            continue
        if tag:
            tags = [t.lower() for t in (product.tags or [])]
            if tag.lower() not in tags:
                continue
        items.append(
            {
                "id": product.id,
                "name": f"Product {product.id}",
                "description": idea.description,
                "image_url": product.image_url,
                "rating": product.rating,
                "tags": product.tags or [],
                "category": trend.category,
            }
        )

    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]
