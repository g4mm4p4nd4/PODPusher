from typing import Dict
from sqlmodel import select

from ..models import ABTest, ABVariant
from ..common.database import get_session


async def create_test(var_a: Dict, var_b: Dict) -> int:
    async with get_session() as session:
        test = ABTest()
        session.add(test)
        await session.commit()
        await session.refresh(test)
        test_id = test.id
        for name, variant in [("A", var_a), ("B", var_b)]:
            db_variant = ABVariant(
                test_id=test.id,
                variant_name=name,
                title=variant.get("title", ""),
                description=variant.get("description", ""),
                tags=variant.get("tags", []),
            )
            session.add(db_variant)
        await session.commit()
        return test_id


async def record_impression(test_id: int, variant_name: str) -> None:
    async with get_session() as session:
        result = await session.exec(
            select(ABVariant).where(
                ABVariant.test_id == test_id,
                ABVariant.variant_name == variant_name,
            )
        )
        variant = result.one()
        variant.impressions += 1
        session.add(variant)
        await session.commit()


async def record_click(test_id: int, variant_name: str) -> None:
    async with get_session() as session:
        result = await session.exec(
            select(ABVariant).where(
                ABVariant.test_id == test_id,
                ABVariant.variant_name == variant_name,
            )
        )
        variant = result.one()
        variant.clicks += 1
        session.add(variant)
        await session.commit()


async def get_metrics(test_id: int) -> Dict:
    async with get_session() as session:
        result = await session.exec(
            select(ABVariant).where(ABVariant.test_id == test_id)
        )
        variants = result.all()
        if not variants:
            return {}
        metrics = []
        for v in variants:
            rate = v.clicks / v.impressions if v.impressions else 0.0
            metrics.append(
                {
                    "variant": v.variant_name,
                    "title": v.title,
                    "description": v.description,
                    "tags": v.tags,
                    "impressions": v.impressions,
                    "clicks": v.clicks,
                    "conversion_rate": rate,
                }
            )
        return {"id": test_id, "variants": metrics}
