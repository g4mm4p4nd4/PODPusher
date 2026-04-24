from typing import List, Optional

from sqlmodel import select
from datetime import datetime

from ..common.database import get_session
from ..models import ABTest, ABVariant, ExperimentType


def _variant_dict(variant: ABVariant, test: ABTest) -> dict:
    rate = (variant.clicks / variant.impressions) if variant.impressions else 0
    return {
        "id": variant.id,
        "test_id": variant.test_id,
        "name": variant.name,
        "weight": variant.weight,
        "impressions": variant.impressions,
        "clicks": variant.clicks,
        "conversion_rate": rate,
        "experiment_type": test.experiment_type,
        "product_id": test.product_id,
        "status": test.status,
        "winner_variant_id": test.winner_variant_id,
        "start_time": test.start_time,
        "end_time": test.end_time,
    }


async def create_test(
    name: str,
    experiment_type: ExperimentType,
    variants: List[dict],
    product_id: int | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict:
    """Create a new A/B test with variants."""
    if not variants:
        raise ValueError("At least one variant required")
    total = sum(v.get('weight', 0) for v in variants)
    if any(v.get('weight', 0) <= 0 for v in variants) or abs(total - 1.0) > 1e-6:
        raise ValueError("Variant weights must be positive and sum to 1")
    async with get_session() as session:
        test = ABTest(
            name=name,
            experiment_type=experiment_type,
            product_id=product_id,
            start_time=start_time,
            end_time=end_time,
        )
        session.add(test)
        await session.commit()
        await session.refresh(test)
        variant_dicts = []
        for v in variants:
            variant = ABVariant(test_id=test.id, name=v['name'], weight=v['weight'])
            session.add(variant)
            await session.commit()
            await session.refresh(variant)
            variant_dicts.append(_variant_dict(variant, test))
        return {
            "id": test.id,
            "name": test.name,
            "experiment_type": test.experiment_type,
            "product_id": test.product_id,
            "status": test.status,
            "start_time": test.start_time,
            "end_time": test.end_time,
            "variants": variant_dicts,
        }


async def get_metrics(test_id: int | None = None) -> List[dict]:
    """Return metrics for all variants or those belonging to a specific test."""
    async with get_session() as session:
        stmt = select(ABVariant, ABTest).join(ABTest, ABVariant.test_id == ABTest.id)
        if test_id is not None:
            stmt = stmt.where(ABVariant.test_id == test_id)
        result = await session.exec(stmt)
        rows = result.all()
        return [_variant_dict(v, t) for v, t in rows]


async def record_click(variant_id: int) -> Optional[dict]:
    """Increment click count for a variant."""
    async with get_session() as session:
        variant = await session.get(ABVariant, variant_id)
        if not variant:
            return None
        test = await session.get(ABTest, variant.test_id)
        now = datetime.utcnow()
        if (test.start_time and now < test.start_time) or (
            test.end_time and now > test.end_time
        ):
            return None
        variant.clicks += 1
        session.add(variant)
        await session.commit()
        await session.refresh(variant)
        return _variant_dict(variant, test)


async def record_impression(variant_id: int) -> Optional[dict]:
    """Increment impression count for a variant."""
    async with get_session() as session:
        variant = await session.get(ABVariant, variant_id)
        if not variant:
            return None
        test = await session.get(ABTest, variant.test_id)
        now = datetime.utcnow()
        if (test.start_time and now < test.start_time) or (
            test.end_time and now > test.end_time
        ):
            return None
        variant.impressions += 1
        session.add(variant)
        await session.commit()
        await session.refresh(variant)
        return _variant_dict(variant, test)


async def pause_test(test_id: int) -> Optional[dict]:
    async with get_session() as session:
        test = await session.get(ABTest, test_id)
        if not test:
            return None
        test.status = "paused"
        session.add(test)
        await session.commit()
        await session.refresh(test)
        return {"id": test.id, "status": test.status}


async def end_test(test_id: int) -> Optional[dict]:
    async with get_session() as session:
        test = await session.get(ABTest, test_id)
        if not test:
            return None
        variants = (
            await session.exec(select(ABVariant).where(ABVariant.test_id == test_id))
        ).all()
        winner = max(
            variants,
            key=lambda item: (
                (item.clicks / item.impressions) if item.impressions else 0
            ),
            default=None,
        )
        test.status = "completed"
        test.end_time = datetime.utcnow()
        test.winner_variant_id = winner.id if winner else None
        session.add(test)
        await session.commit()
        await session.refresh(test)
        return {
            "id": test.id,
            "status": test.status,
            "winner_variant_id": test.winner_variant_id,
        }


async def duplicate_test(test_id: int) -> Optional[dict]:
    async with get_session() as session:
        test = await session.get(ABTest, test_id)
        if not test:
            return None
        variants = (
            await session.exec(select(ABVariant).where(ABVariant.test_id == test_id))
        ).all()
    return await create_test(
        f"{test.name} Copy",
        test.experiment_type,
        [{"name": variant.name, "weight": variant.weight} for variant in variants],
        test.product_id,
        None,
        None,
    )


async def push_winner(test_id: int) -> Optional[dict]:
    async with get_session() as session:
        test = await session.get(ABTest, test_id)
        if not test:
            return None
        if not test.winner_variant_id:
            variants = (
                await session.exec(
                    select(ABVariant).where(ABVariant.test_id == test_id)
                )
            ).all()
            winner = max(
                variants,
                key=lambda item: (
                    (item.clicks / item.impressions) if item.impressions else 0
                ),
                default=None,
            )
            test.winner_variant_id = winner.id if winner else None
        if not test.winner_variant_id:
            return None
        winner = await session.get(ABVariant, test.winner_variant_id)
        if not winner:
            return None
        test.status = "pushed"
        session.add(test)
        await session.commit()
        return {
            "test_id": test.id,
            "winner_variant_id": winner.id,
            "winner": winner.name,
            "status": "pushed",
        }
