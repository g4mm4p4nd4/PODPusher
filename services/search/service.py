from typing import List, Optional, Dict
from sqlalchemy import or_, func
from sqlmodel import select

from ..models import Product, Idea, Trend
from ..common.database import get_session


async def search_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    rating_min: Optional[int] = None,
    offset: int = 0,
    limit: int = 10,
) -> Dict[str, List[Dict]]:
    """Search products with optional filters and pagination."""

    async with get_session() as session:
        stmt = (
            select(Product, Idea, Trend)
            .join(Idea, Product.idea_id == Idea.id)
            .join(Trend, Idea.trend_id == Trend.id)
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
            stmt = stmt.where(Trend.category == category)
        if rating_min is not None:
            stmt = stmt.where(Product.rating >= rating_min)

        result = await session.exec(stmt)
        rows = result.all()

        if tag:
            rows = [r for r in rows if tag in ((r[0].tags) or [])]

        total = len(rows)
        rows = rows[offset : offset + limit]

        items = [
            {
                "id": p.id,
                "name": f"Product {p.id}",
                "description": idea.description,
                "category": trend.category,
                "image_url": p.image_url,
                "rating": p.rating,
                "tags": p.tags or [],
            }
            for p, idea, trend in rows
        ]
        return {"total": total, "items": items}
