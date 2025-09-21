"""Data access helpers for product review workflows."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Optional

from sqlmodel import select

from ..common.database import get_session
from ..models import Product

DEFAULT_REVIEW_LIMIT = 50


async def fetch_latest_products(limit: int = DEFAULT_REVIEW_LIMIT) -> list[Product]:
    """Return the most recent products ordered by ``created_at`` descending."""
    async with get_session() as session:
        statement = (
            select(Product)
            .order_by(Product.created_at.desc())
            .limit(limit)
        )
        result = await session.exec(statement)
        # SQLModel returns a Sequence; coerce to list for callers.
        products: Sequence[Product] = result.all()
        return list(products)


async def persist_product_update(
    product_id: int,
    *,
    rating: Optional[int] = None,
    tags: Optional[list[str]] = None,
    flagged: Optional[bool] = None,
) -> Optional[Product]:
    """Update mutable review fields for a product.

    Args:
        product_id: Identifier of the product to update.
        rating: Optional rating value expected to be between 1 and 5.
        tags: Optional list of user supplied tags.
        flagged: Optional moderation flag.

    Returns:
        The updated :class:`Product` instance or ``None`` if the product does
        not exist.

    Raises:
        ValueError: If ``rating`` is outside the inclusive range ``[1, 5]``.
    """

    if rating is not None and not 1 <= rating <= 5:
        raise ValueError("rating must be between 1 and 5")

    async with get_session() as session:
        product = await session.get(Product, product_id)
        if product is None:
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
        return product
