from typing import List, Optional
from sqlmodel import select

from ..common.database import get_session
from ..models import ABTest, ABVariant


async def create_test(
    title: str,
    description: str,
    variant_a: str,
    variant_b: str,
    tags_a: Optional[List[str]] = None,
    tags_b: Optional[List[str]] = None,
) -> int:
    """Create a new A/B test with two variants."""
    async with get_session() as session:
        test = ABTest(title=title, description=description)
        session.add(test)
        await session.commit()
        await session.refresh(test)
        test_id = test.id
        session.add(ABVariant(test_id=test_id, variant_name=variant_a, tags=tags_a))
        session.add(ABVariant(test_id=test_id, variant_name=variant_b, tags=tags_b))
        await session.commit()
        return test_id


async def get_metrics(test_id: int) -> List[dict]:
    """Return metrics per variant."""
    async with get_session() as session:
        result = await session.exec(
            select(ABVariant).where(ABVariant.test_id == test_id)
        )
        variants = result.all()
        metrics = []
        for v in variants:
            conversion = v.clicks / v.impressions if v.impressions else 0.0
            metrics.append(
                {
                    "variant_name": v.variant_name,
                    "impressions": v.impressions,
                    "clicks": v.clicks,
                    "conversion_rate": conversion,
                }
            )
        return metrics


async def record_click(test_id: int, variant_name: str) -> None:
    """Increment click count for a variant."""
    async with get_session() as session:
        result = await session.exec(
            select(ABVariant).where(
                ABVariant.test_id == test_id, ABVariant.variant_name == variant_name
            )
        )
        variant = result.one_or_none()
        if variant:
            variant.clicks += 1
            session.add(variant)
            await session.commit()


async def record_impression(test_id: int, variant_name: str) -> None:
    """Increment impression count for a variant."""
    async with get_session() as session:
        result = await session.exec(
            select(ABVariant).where(
                ABVariant.test_id == test_id, ABVariant.variant_name == variant_name
            )
        )
        variant = result.one_or_none()
        if variant:
            variant.impressions += 1
            session.add(variant)
            await session.commit()
