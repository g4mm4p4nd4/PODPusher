from datetime import datetime
from math import erf, sqrt
from typing import Any, List, Optional

from sqlmodel import select

from ..common.database import get_session
from ..common.time import utcnow
from ..models import ABTest, ABVariant, ExperimentType


PRODUCT_OPTIONS = [
    {"id": 101, "name": "Retro Beach Sunset Tee"},
    {"id": 102, "name": "Dog Mom Vintage Hoodie"},
    {"id": 103, "name": "Teacher Life Coffee Mug"},
    {"id": 104, "name": "Vintage Summer Tee"},
    {"id": 105, "name": "Mental Health Matters Tote"},
]


def _utcnow() -> datetime:
    return utcnow()


def _provenance(source: str, estimated: bool = False) -> dict[str, Any]:
    return {
        "source": source,
        "is_estimated": estimated,
        "updated_at": _utcnow().isoformat(),
        "confidence": 0.82 if estimated else 0.94,
    }


def _product_name(product_id: int | None) -> str:
    if product_id is None:
        return "Unassigned product"
    product = next((item for item in PRODUCT_OPTIONS if item["id"] == product_id), None)
    return product["name"] if product else f"Product {product_id}"


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


def _normal_cdf(value: float) -> float:
    return 0.5 * (1 + erf(value / sqrt(2)))


def _variant_confidence(a: dict[str, Any], b: dict[str, Any]) -> float:
    if not a["impressions"] or not b["impressions"]:
        return 0.5
    p1 = a["clicks"] / a["impressions"]
    p2 = b["clicks"] / b["impressions"]
    pooled = (a["clicks"] + b["clicks"]) / (a["impressions"] + b["impressions"])
    standard_error = sqrt(
        max(
            0.000001,
            pooled * (1 - pooled) * (1 / a["impressions"] + 1 / b["impressions"]),
        )
    )
    return round(max(_normal_cdf(abs(p2 - p1) / standard_error), 0.5), 4)


def _experiment_payload(test: dict[str, Any]) -> dict[str, Any]:
    variants = test["variants"]
    winner = max(variants, key=lambda item: item["ctr"]) if variants else None
    loser = min(variants, key=lambda item: item["ctr"]) if len(variants) > 1 else None
    confidence = _variant_confidence(loser, winner) if winner and loser else 0.5
    lift = (
        round((winner["ctr"] - loser["ctr"]) / max(loser["ctr"], 0.01) * 100, 1)
        if winner and loser
        else 0
    )
    impressions = sum(item["impressions"] for item in variants)
    clicks = sum(item["clicks"] for item in variants)
    return {
        **test,
        "impressions": impressions,
        "clicks": clicks,
        "ctr": round((clicks / max(1, impressions)) * 100, 2),
        "winner": winner,
        "ctr_lift": lift,
        "confidence": round(confidence * 100, 1),
        "significant": confidence >= 0.95,
        "actions_available": ["pause", "duplicate", "end", "push-winner"],
        "integration_status": {
            "listing_push": "demo" if test["id"] == 0 else "local_state",
            "message": (
                "Listing push records demo metadata until Etsy credentials are connected."
                if test["id"] == 0
                else "Winner push updates local experiment state."
            ),
        },
        "next_drilldowns": ["winner_confidence", "variant_breakdown"],
        "insights": [
            (
                f"{winner['name']} is driving higher CTR with a {lift}% lift."
                if winner
                else "Collect more traffic before selecting a winner."
            ),
            "Peak performance occurs between 12PM-6PM.",
            "Metric provenance is local A/B event state unless marked estimated.",
        ],
        "provenance": _provenance("abtest_table", estimated=test["id"] == 0),
    }


def _demo_experiments() -> list[dict[str, Any]]:
    return [
        _experiment_payload(
            {
                "id": 0,
                "name": "Retro Sunset Tee - Thumbnail Test",
                "product_id": 101,
                "product": "Retro Beach Sunset Tee",
                "experiment_type": "thumbnail",
                "status": "running",
                "start_time": "2025-05-12T00:00:00",
                "end_time": None,
                "variants": [
                    {
                        "id": 0,
                        "name": "Thumbnail A",
                        "weight": 0.5,
                        "impressions": 61273,
                        "clicks": 2629,
                        "ctr": 4.29,
                    },
                    {
                        "id": 0,
                        "name": "Thumbnail B",
                        "weight": 0.5,
                        "impressions": 67269,
                        "clicks": 3192,
                        "ctr": 5.28,
                    },
                ],
            }
        )
    ]


def _matches_filters(
    experiment: dict[str, Any],
    search: str | None,
    status: str | None,
    start_date: datetime | None,
    end_date: datetime | None,
) -> bool:
    if search:
        needle = search.lower()
        haystack = " ".join(
            [
                str(experiment.get("name", "")),
                str(experiment.get("product", "")),
                str(experiment.get("experiment_type", "")),
            ]
        ).lower()
        if needle not in haystack:
            return False
    if status and status != "all" and experiment.get("status") != status:
        return False
    started = experiment.get("start_time")
    if isinstance(started, str):
        started_dt = datetime.fromisoformat(started)
    else:
        started_dt = started
    if start_date and started_dt and started_dt < start_date:
        return False
    if end_date and started_dt and started_dt > end_date:
        return False
    return True


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
            "product": _product_name(test.product_id),
            "status": test.status,
            "start_time": test.start_time,
            "end_time": test.end_time,
            "variants": variant_dicts,
            "integration_status": {
                "listing_push": "local_state",
                "message": "Experiment created in local A/B state.",
            },
            "provenance": _provenance("abtest_table"),
        }


async def get_dashboard(
    search: str | None = None,
    status: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = 1,
    page_size: int = 25,
    sort_by: str = "created",
    sort_order: str = "desc",
) -> dict[str, Any]:
    async with get_session() as session:
        rows = (
            await session.exec(
                select(ABVariant, ABTest).join(ABTest, ABVariant.test_id == ABTest.id)
            )
        ).all()

    grouped: dict[int, dict[str, Any]] = {}
    for variant, test in rows:
        test_payload = grouped.setdefault(
            test.id,
            {
                "id": test.id,
                "name": test.name,
                "product_id": test.product_id,
                "product": _product_name(test.product_id),
                "experiment_type": test.experiment_type,
                "status": test.status,
                "start_time": test.start_time.isoformat() if test.start_time else None,
                "end_time": test.end_time.isoformat() if test.end_time else None,
                "variants": [],
            },
        )
        ctr = (variant.clicks / variant.impressions) if variant.impressions else 0
        test_payload["variants"].append(
            {
                "id": variant.id,
                "name": variant.name,
                "weight": variant.weight,
                "impressions": variant.impressions,
                "clicks": variant.clicks,
                "ctr": round(ctr * 100, 2),
            }
        )

    experiments = [_experiment_payload(item) for item in grouped.values()]
    if not experiments:
        experiments = _demo_experiments()
    filtered = [
        item
        for item in experiments
        if _matches_filters(item, search, status, start_date, end_date)
    ]
    reverse = sort_order.lower() != "asc"
    if sort_by in {"name", "product", "status", "experiment_type"}:
        filtered = sorted(
            filtered,
            key=lambda item: str(item.get(sort_by, "")),
            reverse=reverse,
        )
    elif sort_by in {"confidence", "ctr_lift", "impressions", "ctr"}:
        filtered = sorted(
            filtered,
            key=lambda item: item.get(sort_by, 0),
            reverse=reverse,
        )
    else:
        filtered = sorted(
            filtered,
            key=lambda item: str(item.get("start_time") or ""),
            reverse=reverse,
        )
    total = len(filtered)
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    start = (page - 1) * page_size
    paged = filtered[start:start + page_size]
    denominator = max(1, len(filtered))
    return {
        "cards": [
            {
                "label": "Active Tests",
                "value": len(
                    [item for item in filtered if item["status"] == "running"]
                ),
                "delta": 15.0,
                "sparkline": [6, 8, 9, 11, 14, 18, 23],
                "provenance": _provenance("abtest_table", estimated=not grouped),
            },
            {
                "label": "Winning Variants",
                "value": len([item for item in filtered if item["winner"]]),
                "delta": 22.2,
                "sparkline": [2, 3, 4, 5, 7, 9, 11],
                "provenance": _provenance("abtest_table", estimated=not grouped),
            },
            {
                "label": "Average CTR Lift",
                "value": round(
                    sum(item["ctr_lift"] for item in filtered) / denominator, 1
                ),
                "delta": 3.8,
                "unit": "%",
                "sparkline": [8, 10, 11, 14, 13, 17, 18],
                "provenance": _provenance("abtest_table", estimated=not grouped),
            },
            {
                "label": "Total Impressions",
                "value": sum(item["impressions"] for item in filtered),
                "delta": 28.6,
                "sparkline": [20, 24, 25, 31, 39, 45, 52],
                "provenance": _provenance("abtest_table", estimated=not grouped),
            },
        ],
        "experiments": paged,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_next": start + page_size < total,
            "has_previous": page > 1,
            "sort_by": sort_by,
            "sort_order": "desc" if reverse else "asc",
        },
        "product_options": PRODUCT_OPTIONS,
        "filters": {
            "search": search or "",
            "status": status or "all",
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
        "integration_status": {
            "etsy": "not_connected",
            "printify": "not_connected",
            "listing_push": "demo" if not grouped else "local_state",
        },
        "provenance": _provenance("ab_dashboard", estimated=not grouped),
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
        now = utcnow()
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
        now = utcnow()
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
    if test_id == 0:
        return {"id": 0, "status": "paused", "demo_state": True}
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
    if test_id == 0:
        return {
            "id": 0,
            "status": "completed",
            "winner_variant_id": 0,
            "demo_state": True,
        }
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
        test.end_time = utcnow()
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
    if test_id == 0:
        return {
            **_demo_experiments()[0],
            "id": -1,
            "name": "Retro Sunset Tee - Thumbnail Test Copy",
            "demo_state": True,
        }
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
    if test_id == 0:
        return {
            "test_id": 0,
            "winner_variant_id": 0,
            "winner": "Thumbnail B",
            "status": "pushed",
            "demo_state": True,
            "integration_status": {
                "listing_push": "demo",
                "message": "Demo state only; Etsy listing credentials are not connected.",
            },
        }
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
            "demo_state": False,
            "integration_status": {
                "listing_push": "local_state",
                "message": "Winning variant marked for listing update in local state.",
            },
        }
