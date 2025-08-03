from typing import List, Optional

from sqlmodel import select

from ..common.database import get_session
from ..models import ABTest, ABVariant


def _variant_dict(variant: ABVariant) -> dict:
    rate = (variant.clicks / variant.impressions) if variant.impressions else 0
    return {
        "id": variant.id,
        "test_id": variant.test_id,
        "listing_id": variant.listing_id,
        "title": variant.title,
        "description": variant.description,
        "impressions": variant.impressions,
        "clicks": variant.clicks,
        "conversion_rate": rate,
    }


async def create_test(name: str, variants: List[dict]) -> dict:
    """Create a new A/B test with variants."""
    async with get_session() as session:
        test = ABTest(name=name)
        session.add(test)
        await session.commit()
        await session.refresh(test)
        test_id = test.id
        variant_dicts = []
        for v in variants:
            variant = ABVariant(
                test_id=test_id,
                listing_id=v["listing_id"],
                title=v["title"],
                description=v["description"],
            )
            session.add(variant)
            await session.commit()
            await session.refresh(variant)
            variant_dicts.append(_variant_dict(variant))
        return {"id": test_id, "name": test.name, "variants": variant_dicts}


async def get_metrics(test_id: int | None = None) -> List[dict]:
    """Return metrics for all variants or those belonging to a specific test."""
    async with get_session() as session:
        stmt = select(ABVariant)
        if test_id is not None:
            stmt = stmt.where(ABVariant.test_id == test_id)
        result = await session.exec(stmt)
        variants = result.all()
        return [_variant_dict(v) for v in variants]


async def record_click(variant_id: int) -> Optional[dict]:
    """Increment click count for a variant."""
    async with get_session() as session:
        variant = await session.get(ABVariant, variant_id)
        if not variant:
            return None
        variant.clicks += 1
        session.add(variant)
        await session.commit()
        await session.refresh(variant)
        return _variant_dict(variant)


async def record_impression(variant_id: int) -> Optional[dict]:
    """Increment impression count for a variant."""
    async with get_session() as session:
        variant = await session.get(ABVariant, variant_id)
        if not variant:
            return None
        variant.impressions += 1
        session.add(variant)
        await session.commit()
        await session.refresh(variant)
        return _variant_dict(variant)
