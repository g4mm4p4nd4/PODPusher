import pytest
from services.ab_test.service import (
    create_test,
    get_metrics,
    record_click,
    record_impression,
)
from services.common.database import init_db


@pytest.mark.asyncio
async def test_ab_test_metrics():
    await init_db()
    test_id = await create_test(
        "Title",
        "Desc",
        "A",
        "B",
        ["t1"],
        ["t2"],
    )
    metrics = await get_metrics(test_id)
    assert len(metrics) == 2
    await record_impression(test_id, "A")
    await record_click(test_id, "A")
    metrics = await get_metrics(test_id)
    a = next(m for m in metrics if m["variant_name"] == "A")
    assert a["impressions"] == 1
    assert a["clicks"] == 1
    assert a["conversion_rate"] == 1.0
