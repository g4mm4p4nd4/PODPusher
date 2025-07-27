from __future__ import annotations
from typing import List, Optional
from sqlalchemy import select, or_, func
from ..models import Product, Idea, Trend
from ..common.database import get_session


async def search_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    rating_min: Optional[int] = None,
    rating_max: Optional[int] = None,
    sort: Optional[str] = None,
) -> List[dict]:
    """Search products and trends using filters."""

    stmt = (
        select(Product, Idea, Trend)
        .join(Idea, Product.idea_id == Idea.id, isouter=True)
        .join(Trend, Idea.trend_id == Trend.id, isouter=True)
    )

    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Idea.description).like(pattern),
                func.lower(Trend.term).like(pattern),
            )
        )
    if category:
        stmt = stmt.where(func.lower(Trend.category) == category.lower())
    if tags:
        for tag in tags:
            stmt = stmt.where(func.json_contains(Product.tags, f'"{tag}"') == 1)
    if rating_min is not None:
        stmt = stmt.where(Product.rating >= rating_min)
    if rating_max is not None:
        stmt = stmt.where(Product.rating <= rating_max)

    if sort == "rating":
        stmt = stmt.order_by(Product.rating.desc().nullslast())
    else:
        stmt = stmt.order_by(Product.created_at.desc())

    async with get_session() as session:
        result = await session.exec(stmt)
        records = result.all()

    results = []
    for product, idea, trend in records:
        results.append(
            {
                "id": product.id,
                "image_url": product.image_url,
                "rating": product.rating,
                "tags": product.tags or [],
                "idea": idea.description if idea else None,
                "term": trend.term if trend else None,
                "category": trend.category if trend else None,
            }
        )
    return results
