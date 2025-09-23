import asyncio
import sys
import types
from types import SimpleNamespace

import pytest


class _DummyTask:
    def __init__(self, func):
        self.run = func

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)


class _DummyCelery:
    def __init__(self, *args, **kwargs):
        self.conf = SimpleNamespace()

    def task(self, func=None, **_options):
        def decorator(f):
            return _DummyTask(f)

        if func is not None:
            return decorator(func)
        return decorator


celery_module = types.ModuleType("celery")
celery_module.Celery = _DummyCelery
sys.modules.setdefault("celery", celery_module)

pytrends_module = types.ModuleType("pytrends")
pytrends_request_module = types.ModuleType("pytrends.request")


class _DummyTrendReq:  # pragma: no cover - only needed for import side effects
    def __init__(self, *args, **kwargs):
        self.kw_list = []


pytrends_request_module.TrendReq = _DummyTrendReq
pytrends_module.request = pytrends_request_module
sys.modules.setdefault("pytrends", pytrends_module)
sys.modules.setdefault("pytrends.request", pytrends_request_module)

from services import tasks


@pytest.mark.parametrize(
    "task_name, service_attr, args, expected",
    [
        ("fetch_trends_task", "fetch_trends", (), ["trend"]),
        (
            "generate_ideas_task",
            "generate_ideas",
            ([{"term": "cats"}],),
            [{"description": "cat shirt"}],
        ),
        (
            "generate_images_task",
            "generate_images",
            (["idea"],),
            [{"image_url": "http://example.com"}],
        ),
        (
            "create_sku_task",
            "create_sku",
            ([{"image_url": "http://example.com"}],),
            [{"sku": "sku-1"}],
        ),
        (
            "publish_listing_task",
            "publish_listing",
            ({"sku": "sku-1"},),
            {"listing_id": 123},
        ),
    ],
)
def test_tasks_return_concrete_results(monkeypatch, task_name, service_attr, args, expected):
    async def fake_service(*_args, **_kwargs):
        return expected

    monkeypatch.setattr(tasks, service_attr, fake_service)
    task = getattr(tasks, task_name)

    result = task.run(*args)

    assert result == expected
    assert not asyncio.iscoroutine(result)


def test_generate_social_post_task_accepts_dict(monkeypatch):
    payload = {"title": "Hello"}
    observed = {}

    async def fake_generate_post(data):
        observed["data"] = data
        return {"caption": "Hello world"}

    monkeypatch.setattr(tasks, "generate_post", fake_generate_post)

    result = tasks.generate_social_post_task.run(payload)

    assert observed["data"] is payload
    assert result == {"caption": "Hello world"}
    assert not asyncio.iscoroutine(result)
