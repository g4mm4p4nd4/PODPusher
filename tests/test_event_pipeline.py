from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from services.orchestrator import api as orchestrator_api
from services.orchestrator import workers


class DummyBroker:
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict]] = []

    async def publish(self, stream: str, message: dict) -> str:
        self.messages.append((stream, message))
        return "1-0"


class FakeScheduler:
    def __init__(self) -> None:
        self.running = False
        self.jobs: dict[str, dict] = {}

    def start(self) -> None:
        self.running = True

    def shutdown(self, wait: bool = False) -> None:
        self.running = False

    def add_job(
        self,
        func,
        trigger: str,
        *,
        seconds: int,
        id: str,
        kwargs: dict,
        replace_existing: bool,
    ) -> None:
        self.jobs[id] = {
            "func": func,
            "trigger": trigger,
            "seconds": seconds,
            "kwargs": kwargs,
            "replace_existing": replace_existing,
        }

    def get_job(self, job_id: str):
        return self.jobs.get(job_id)

    def remove_job(self, job_id: str) -> None:
        self.jobs.pop(job_id, None)

    def remove_all_jobs(self) -> None:
        self.jobs.clear()


@pytest.mark.asyncio
async def test_handle_trend_ignores_missing_user_id_or_trend(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_broker = DummyBroker()
    monkeypatch.setattr(workers, "broker", dummy_broker)

    async def fail_post(*args, **kwargs):
        raise AssertionError("pipeline should not call downstream services")

    monkeypatch.setattr(workers, "_post_json", fail_post)

    await workers.handle_trend({})
    await workers.handle_trend({"user_id": 9})
    await workers.handle_trend({"trend": "cats"})

    assert dummy_broker.messages == []


@pytest.mark.asyncio
async def test_pipeline_preserves_user_id_and_current_contracts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy_broker = DummyBroker()
    monkeypatch.setattr(workers, "broker", dummy_broker)

    calls: list[tuple[str, str, dict, dict | None]] = []

    async def fake_post_json(
        base_url: str,
        path: str,
        payload: dict,
        *,
        headers: dict[str, str] | None = None,
    ):
        calls.append((base_url, path, payload, headers))

        if base_url == workers.IDEATION_URL and path == "/ideas":
            assert payload == {"trends": ["cats"]}
            return [
                {
                    "id": 11,
                    "term": "cats",
                    "category": "animals",
                    "description": "Cat mug with floral outline",
                }
            ]

        if base_url == workers.IMAGE_URL and path == "/generate":
            assert headers == {"X-User-Id": "42"}
            return [
                {
                    "id": 21,
                    "idea_id": 11,
                    "image_url": "https://example.com/cat-mug.png",
                    "category": "animals",
                }
            ]

        if base_url == workers.INTEGRATION_URL and path == "/sku":
            assert headers == {"X-User-Id": "42"}
            assert payload["products"][0]["idea_id"] == 11
            return [{**payload["products"][0], "sku": "sku-1"}]

        if base_url == workers.INTEGRATION_URL and path == "/listing":
            assert headers == {"X-User-Id": "42"}
            assert payload["sku"] == "sku-1"
            return {"listing_id": "listing-1", "etsy_url": "https://etsy.test/listing-1"}

        if base_url == workers.NOTIFICATIONS_URL and path == "/":
            assert headers == {"X-User-Id": "42"}
            return {"id": 1}

        raise AssertionError(f"unexpected request {base_url}{path}")

    monkeypatch.setattr(workers, "_post_json", fake_post_json)

    await workers.handle_trend({"user_id": 42, "trend": "cats", "source": "manual", "auto": False})
    assert dummy_broker.messages[0][0] == workers.IDEAS_READY_STREAM
    ideas_event = dummy_broker.messages[0][1]
    assert ideas_event["user_id"] == 42

    await workers.handle_ideas(ideas_event)
    assert dummy_broker.messages[1][0] == workers.IMAGES_READY_STREAM
    images_event = dummy_broker.messages[1][1]
    assert images_event["user_id"] == 42

    await workers.handle_images(images_event)
    assert dummy_broker.messages[2][0] == workers.PRODUCTS_READY_STREAM
    products_event = dummy_broker.messages[2][1]
    assert products_event["user_id"] == 42

    await workers.handle_products(products_event)
    assert dummy_broker.messages[3][0] == workers.LISTINGS_READY_STREAM
    listing_event = dummy_broker.messages[3][1]
    assert listing_event["user_id"] == 42
    assert listing_event["listing"]["etsy_url"] == "https://etsy.test/listing-1"

    assert [(base, path) for base, path, _, _ in calls] == [
        (workers.IDEATION_URL, "/ideas"),
        (workers.NOTIFICATIONS_URL, "/"),
        (workers.IMAGE_URL, "/generate"),
        (workers.NOTIFICATIONS_URL, "/"),
        (workers.INTEGRATION_URL, "/sku"),
        (workers.NOTIFICATIONS_URL, "/"),
        (workers.INTEGRATION_URL, "/listing"),
        (workers.NOTIFICATIONS_URL, "/"),
    ]


@pytest.mark.asyncio
async def test_register_periodic_trend_signal_publishes_user_scoped_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy_broker = DummyBroker()
    fake_scheduler = FakeScheduler()

    monkeypatch.setattr(workers, "broker", dummy_broker)
    monkeypatch.setattr(workers, "scheduler", fake_scheduler)
    monkeypatch.setattr(workers, "_scheduled_jobs", {})

    schedule = workers.register_periodic_trend_signal(
        user_id=5,
        trend="cats",
        interval_seconds=60,
        source="scheduled",
    )

    assert schedule["user_id"] == 5
    assert fake_scheduler.running is True
    assert schedule["job_id"] in fake_scheduler.jobs

    job = fake_scheduler.jobs[schedule["job_id"]]
    await job["func"](**job["kwargs"])

    assert dummy_broker.messages == [
        (
            workers.TREND_SIGNALS_STREAM,
            {
                "user_id": 5,
                "trend": "cats",
                "source": "scheduled",
                "auto": True,
            },
        )
    ]

    assert workers.remove_periodic_trend_signal(job_id=schedule["job_id"], user_id=5) is True


@pytest.mark.asyncio
async def test_schedule_endpoint_requires_auth_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_start() -> None:
        return None

    async def fake_stop() -> None:
        return None

    monkeypatch.setattr(orchestrator_api, "start", fake_start)
    monkeypatch.setattr(orchestrator_api, "stop", fake_stop)

    transport = ASGITransport(app=orchestrator_api.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/schedules/trend", json={"trend": "cats", "interval_seconds": 60})

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_enqueue_endpoint_uses_authenticated_user_id(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_start() -> None:
        return None

    async def fake_stop() -> None:
        return None

    captured: list[dict] = []

    async def fake_publish_trend_signal(*, user_id: int, trend: str, source: str = "manual", auto: bool = False):
        event = {"user_id": user_id, "trend": trend, "source": source, "auto": auto}
        captured.append(event)
        return event

    monkeypatch.setattr(orchestrator_api, "start", fake_start)
    monkeypatch.setattr(orchestrator_api, "stop", fake_stop)
    monkeypatch.setattr(orchestrator_api, "publish_trend_signal", fake_publish_trend_signal)

    transport = ASGITransport(app=orchestrator_api.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/events/trend",
            json={"trend": "cats", "source": "manual"},
            headers={"X-User-Id": "17"},
        )

    assert resp.status_code == 200
    assert captured == [{"user_id": 17, "trend": "cats", "source": "manual", "auto": False}]
