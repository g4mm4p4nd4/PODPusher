import pytest
from services.ab_test.service import (
    create_test,
    record_impression,
    record_click,
    get_metrics,
)
from services.common.database import init_db


@pytest.mark.asyncio
async def test_create_and_metrics():
    await init_db()
    test_id = await create_test(
        {"title": "A", "description": "", "tags": []},
        {"title": "B", "description": "", "tags": []},
    )
    await record_impression(test_id, "A")
    await record_impression(test_id, "A")
    await record_click(test_id, "A")
    data = await get_metrics(test_id)
    assert data["id"] == test_id
    a = next(v for v in data["variants"] if v["variant"] == "A")
    assert a["impressions"] == 2
    assert a["clicks"] == 1
    assert a["conversion_rate"] == 0.5
