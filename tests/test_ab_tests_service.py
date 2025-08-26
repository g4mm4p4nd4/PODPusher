import pytest
from datetime import datetime, timedelta
from services.ab_tests.service import (
    create_test,
    get_metrics,
    record_click,
    record_impression,
)
from services.common.database import init_db


@pytest.mark.asyncio
async def test_ab_service_flow():
    await init_db()
    start = datetime.utcnow()
    end = start + timedelta(days=1)
    test = await create_test(
        "Example",
        ["A", "B"],
        "image",
        [0.6, 0.4],
        start,
        end,
    )
    assert test["name"] == "Example"
    assert test["experiment_type"] == "image"
    assert len(test["variants"]) == 2
    assert test["start_time"]
    vid = test["variants"][0]["id"]
    assert test["variants"][0]["traffic_weight"] == pytest.approx(0.6)
    await record_impression(vid)
    await record_click(vid)
    metrics = await get_metrics(test["id"])
    var = next(v for v in metrics if v["id"] == vid)
    assert var["impressions"] == 1
    assert var["clicks"] == 1
    assert var["conversion_rate"] == 1.0
