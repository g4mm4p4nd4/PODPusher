import pytest
from datetime import datetime, timedelta
from services.ab_tests.service import (
    create_test,
    get_metrics,
    record_click,
    record_impression,
)
from services.common.database import init_db
from services.models import ExperimentType


@pytest.mark.asyncio
async def test_ab_service_flow():
    await init_db()
    test = await create_test(
        "Example",
        ExperimentType.IMAGE,
        [{"name": "A", "weight": 0.7}, {"name": "B", "weight": 0.3}],
    )
    assert test["experiment_type"] == ExperimentType.IMAGE
    vid = test["variants"][0]["id"]
    await record_impression(vid)
    await record_click(vid)
    metrics = await get_metrics(test["id"])
    var = next(v for v in metrics if v["id"] == vid)
    assert var["weight"] == 0.7
    assert var["impressions"] == 1
    assert var["clicks"] == 1
    assert var["conversion_rate"] == 1.0


@pytest.mark.asyncio
async def test_weight_validation():
    await init_db()
    with pytest.raises(ValueError):
        await create_test(
            "Bad",
            ExperimentType.PRICE,
            [{"name": "A", "weight": 0.6}, {"name": "B", "weight": 0.5}],
        )


@pytest.mark.asyncio
async def test_scheduling():
    await init_db()
    future = datetime.utcnow() + timedelta(days=1)
    test = await create_test(
        "Sched",
        ExperimentType.DESCRIPTION,
        [{"name": "A", "weight": 1.0}],
        start_time=future,
    )
    vid = test["variants"][0]["id"]
    assert await record_impression(vid) is None
