"""Search service with database level filtering."""

from typing import Dict, List, Optional

from sqlalchemy import func, or_
from sqlmodel import select

from ..common.database import get_session
from ..models import Idea, Product, Trend


async def search_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    rating_min: Optional[int] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, object]:
    """Filter products by keyword, category, tag and rating using SQL."""

    async with get_session() as session:
        stmt = (
            select(Product, Idea, Trend)
            .join(Idea, Product.idea_id == Idea.id)
            .join(Trend, Idea.trend_id == Trend.id)
        )

        if q:
            like = f"%{q}%"
            stmt = stmt.where(or_(Idea.description.ilike(like), Trend.term.ilike(like)))
        if category:
            stmt = stmt.where(Trend.category == category.lower())
        if rating_min is not None:
            stmt = stmt.where(Product.rating >= rating_min)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.exec(count_stmt)).one()

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await session.exec(stmt)
        rows = result.all()

    items: List[dict] = []
    for product, idea, trend in rows:
        if tag and tag not in (product.tags or []):
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

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
