import pytest
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
    test = await create_test(
        "Example",
        [
            {
                "listing_id": 1,
                "title": "A",
                "description": "First",
            },
            {
                "listing_id": 2,
                "title": "B",
                "description": "Second",
            },
        ],
    )
    assert test["name"] == "Example"
    assert len(test["variants"]) == 2
    vid = test["variants"][0]["id"]
    await record_impression(vid)
    await record_click(vid)
    metrics = await get_metrics(test["id"])
    var = next(v for v in metrics if v["id"] == vid)
    assert var["impressions"] == 1
    assert var["clicks"] == 1
    assert var["conversion_rate"] == 1.0
