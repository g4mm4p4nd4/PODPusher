import asyncio
import importlib
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


class _DummyTrendReq:  # pragma: no cover - only needed for import side effects
    def __init__(self, *args, **kwargs):
        self.kw_list = []


def _load_tasks_module():
    restore_actions = []

    def _set_module(name: str, module: types.ModuleType) -> None:
        previous = sys.modules.get(name)
        sys.modules[name] = module

        def restore_module(prev=previous, target=name, replacement=module):
            current = sys.modules.get(target)
            if prev is not None:
                sys.modules[target] = prev
            elif current is replacement:
                sys.modules.pop(target, None)

        restore_actions.append(restore_module)

    celery_module = types.ModuleType("celery")
    celery_module.Celery = _DummyCelery
    _set_module("celery", celery_module)

    pytrends_module = types.ModuleType("pytrends")
    pytrends_request_module = types.ModuleType("pytrends.request")
    pytrends_request_module.TrendReq = _DummyTrendReq
    pytrends_module.request = pytrends_request_module
    _set_module("pytrends", pytrends_module)
    _set_module("pytrends.request", pytrends_request_module)

    sqlalchemy_module = types.ModuleType("sqlalchemy")

    def _column(*_args, **_kwargs):
        return None

    class _DummyFunc:
        def __getattr__(self, _name):
            return lambda *_args, **_kwargs: None

    def _or_(*_args, **_kwargs):
        return None

    def _case(*_args, **_kwargs):
        return None

    def _count(*_args, **_kwargs):
        return 0

    class _AsyncBeginContext:
        async def __aenter__(self):
            return types.SimpleNamespace(run_sync=lambda fn: fn(None))

        async def __aexit__(self, *_args):
            return False

    class _DummyEngine:
        async def begin(self):
            return _AsyncBeginContext()

    def _create_async_engine(*_args, **_kwargs):
        return _DummyEngine()

    class _DummySession:
        def __init__(self, *_args, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def exec(self, *_args, **_kwargs):
            return types.SimpleNamespace(all=lambda: [], one=lambda: 0)

    sqlalchemy_ext_module = types.ModuleType("sqlalchemy.ext")
    sqlalchemy_asyncio_module = types.ModuleType("sqlalchemy.ext.asyncio")
    sqlalchemy_asyncio_module.create_async_engine = _create_async_engine
    sqlalchemy_asyncio_module.AsyncSession = _DummySession
    sqlalchemy_ext_module.asyncio = sqlalchemy_asyncio_module

    sqlalchemy_sql_module = types.ModuleType("sqlalchemy.sql")
    sqlalchemy_sql_module.func = types.SimpleNamespace(count=_count)
    sqlalchemy_sql_module.case = _case

    sqlalchemy_module.Column = _column
    sqlalchemy_module.JSON = object()
    sqlalchemy_module.func = _DummyFunc()
    sqlalchemy_module.or_ = _or_
    sqlalchemy_module.ext = types.SimpleNamespace(asyncio=sqlalchemy_asyncio_module)

    _set_module("sqlalchemy", sqlalchemy_module)
    _set_module("sqlalchemy.ext", sqlalchemy_ext_module)
    _set_module("sqlalchemy.ext.asyncio", sqlalchemy_asyncio_module)
    _set_module("sqlalchemy.sql", sqlalchemy_sql_module)

    sqlmodel_module = types.ModuleType("sqlmodel")

    class _DummySQLModel:
        def __init_subclass__(cls, **_kwargs):
            return super().__init_subclass__()

    def _field(*_args, default=None, default_factory=None, **_kwargs):
        if default_factory is not None:
            return default_factory()
        return default

    class _DummySelect:
        def join(self, *args, **kwargs):
            return self

        def where(self, *args, **kwargs):
            return self

        def select_from(self, *args, **kwargs):
            return self

        def subquery(self, *args, **kwargs):
            return self

        def offset(self, *args, **kwargs):
            return self

        def limit(self, *args, **kwargs):
            return self

    sqlmodel_module.Field = _field
    sqlmodel_module.SQLModel = _DummySQLModel
    sqlmodel_module.select = lambda *_args, **_kwargs: _DummySelect()

    _DummySQLModel.metadata = types.SimpleNamespace(create_all=lambda *_args, **_kwargs: None)

    sqlmodel_ext_module = types.ModuleType("sqlmodel.ext")
    sqlmodel_asyncio_module = types.ModuleType("sqlmodel.ext.asyncio")
    sqlmodel_asyncio_session_module = types.ModuleType("sqlmodel.ext.asyncio.session")

    sqlmodel_asyncio_session_module.AsyncSession = sqlalchemy_asyncio_module.AsyncSession
    sqlmodel_asyncio_module.session = sqlmodel_asyncio_session_module
    sqlmodel_ext_module.asyncio = sqlmodel_asyncio_module

    _set_module("sqlmodel", sqlmodel_module)
    _set_module("sqlmodel.ext", sqlmodel_ext_module)
    _set_module("sqlmodel.ext.asyncio", sqlmodel_asyncio_module)
    _set_module("sqlmodel.ext.asyncio.session", sqlmodel_asyncio_session_module)

    def _ensure_package(name: str) -> types.ModuleType:
        module = sys.modules.get(name)
        if module is not None:
            return module
        if name == "services":
            return importlib.import_module(name)

        module = types.ModuleType(name)
        module.__path__ = []  # type: ignore[attr-defined]
        _set_module(name, module)

        parent_name, _, child_name = name.rpartition(".")
        if parent_name:
            parent_module = _ensure_package(parent_name)
            setattr(parent_module, child_name, module)

            def restore_parent(parent=parent_module, child=child_name, placeholder=module):
                if getattr(parent, child, None) is placeholder:
                    delattr(parent, child)

            restore_actions.append(restore_parent)
        return module

    def _install_stub(fullname: str, attrs: dict) -> None:
        parent_name, _, child_name = fullname.rpartition(".")
        parent_module = _ensure_package(parent_name) if parent_name else None

        previous = sys.modules.get(fullname)
        module = types.ModuleType(fullname)
        for key, value in attrs.items():
            setattr(module, key, value)

        sys.modules[fullname] = module
        if parent_module:
            setattr(parent_module, child_name, module)

        def restore_stub(
            target=fullname,
            prev=previous,
            parent=parent_module,
            child=child_name,
            replacement=module,
        ):
            current = sys.modules.get(target)
            if prev is not None:
                sys.modules[target] = prev
                if parent:
                    setattr(parent, child, prev)
            else:
                if current is replacement:
                    sys.modules.pop(target, None)
                if parent and getattr(parent, child, None) is replacement:
                    delattr(parent, child)

        restore_actions.append(restore_stub)

    _ensure_package("services")
    _install_stub("services.trend_scraper.service", {"fetch_trends": lambda *_a, **_k: []})
    _install_stub(
        "services.ideation.service",
        {"generate_ideas": lambda *_a, **_k: []},
    )
    _install_stub(
        "services.image_gen.service",
        {"generate_images": lambda *_a, **_k: []},
    )
    _install_stub(
        "services.integration.service",
        {
            "create_sku": lambda *_a, **_k: [],
            "publish_listing": lambda *_a, **_k: {},
        },
    )
    _install_stub(
        "services.social_generator.service",
        {"generate_post": lambda *_a, **_k: {}},
    )

    try:
        return importlib.import_module("services.tasks")
    finally:
        for restore in reversed(restore_actions):
            restore()


tasks = _load_tasks_module()


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
