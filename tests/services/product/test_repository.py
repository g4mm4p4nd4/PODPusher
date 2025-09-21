import pytest
from datetime import datetime, timedelta

from services.common.database import get_session, init_db
from services.models import Product
from services.product.repository import (
    DEFAULT_REVIEW_LIMIT,
    fetch_latest_products,
    persist_product_update,
)


@pytest.mark.asyncio
async def test_fetch_latest_products_limits_and_orders_desc():
    await init_db()
    base_time = datetime.utcnow()

    async with get_session() as session:
        for index in range(DEFAULT_REVIEW_LIMIT + 10):
            product = Product(
                idea_id=index,
                image_url=f"https://example.com/{index}.png",
                created_at=base_time + timedelta(minutes=index),
            )
            session.add(product)
        await session.commit()

    products = await fetch_latest_products()

    assert len(products) == DEFAULT_REVIEW_LIMIT
    assert all(
        products[i].created_at >= products[i + 1].created_at
        for i in range(len(products) - 1)
    )


@pytest.mark.asyncio
async def test_persist_product_update_modifies_fields():
    await init_db()

    async with get_session() as session:
        product = Product(
            idea_id=1,
            image_url="https://example.com/product.png",
            rating=2,
            tags=["initial"],
            flagged=False,
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        product_id = product.id

    updated = await persist_product_update(
        product_id,
        rating=4,
        tags=["updated", "tag"],
        flagged=True,
    )

    assert updated is not None
    assert updated.rating == 4
    assert updated.tags == ["updated", "tag"]
    assert updated.flagged is True

    async with get_session() as session:
        refreshed = await session.get(Product, product_id)
        assert refreshed.rating == 4
        assert refreshed.tags == ["updated", "tag"]
        assert refreshed.flagged is True


@pytest.mark.asyncio
async def test_persist_product_update_enforces_rating_range():
    await init_db()

    async with get_session() as session:
        product = Product(
            idea_id=1,
            image_url="https://example.com/product.png",
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        product_id = product.id

    with pytest.raises(ValueError):
        await persist_product_update(product_id, rating=6)
