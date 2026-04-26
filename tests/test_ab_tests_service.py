import pytest
from datetime import timedelta
from services.common.time import utcnow
from services.ab_tests.service import (
    create_test,
    duplicate_test,
    end_test,
    get_dashboard,
    get_metrics,
    pause_test,
    push_winner,
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
    future = utcnow() + timedelta(days=1)
    test = await create_test(
        "Sched",
        ExperimentType.DESCRIPTION,
        [{"name": "A", "weight": 1.0}],
        start_time=future,
    )
    vid = test["variants"][0]["id"]
    assert await record_impression(vid) is None


@pytest.mark.asyncio
async def test_dashboard_filters_and_action_mutations():
    await init_db()
    first = await create_test(
        "Retro title test",
        ExperimentType.TITLE,
        [{"name": "Title A", "weight": 0.5}, {"name": "Title B", "weight": 0.5}],
        product_id=101,
    )
    second = await create_test(
        "Dog mom thumbnail test",
        ExperimentType.THUMBNAIL,
        [{"name": "Image A", "weight": 0.5}, {"name": "Image B", "weight": 0.5}],
        product_id=102,
    )

    await pause_test(second["id"])
    dashboard = await get_dashboard(search="retro", status="running")
    assert [item["id"] for item in dashboard["experiments"]] == [first["id"]]
    assert dashboard["experiments"][0]["product"] == "Retro Beach Sunset Tee"
    assert dashboard["experiments"][0]["provenance"]["source"] == "abtest_table"

    paused = await pause_test(first["id"])
    assert paused["status"] == "paused"

    duplicated = await duplicate_test(first["id"])
    assert duplicated["name"] == "Retro title test Copy"
    assert duplicated["product_id"] == 101

    ended = await end_test(first["id"])
    assert ended["status"] == "completed"
    assert ended["winner_variant_id"] is not None

    pushed = await push_winner(first["id"])
    assert pushed["status"] == "pushed"
    assert pushed["demo_state"] is False


@pytest.mark.asyncio
async def test_demo_actions_return_explicit_demo_state():
    await init_db()
    pushed = await push_winner(0)
    assert pushed["demo_state"] is True
    assert pushed["integration_status"]["listing_push"] == "demo"
