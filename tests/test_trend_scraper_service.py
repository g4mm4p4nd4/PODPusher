import pytest

from services.common.database import init_db
from services.trend_scraper import service


class _ListLike:
    def __init__(self, values):
        self._values = values

    def tolist(self):
        return list(self._values)


class _RelatedTop:
    def __init__(self, values):
        self._values = values

    def __getitem__(self, key):
        if key != "query":
            raise KeyError(key)
        return _ListLike(self._values)


class _TrendingRows:
    def __init__(self, values):
        self._values = values

    def head(self, _count):
        return self

    def __getitem__(self, key):
        if key != 0:
            raise KeyError(key)
        return _ListLike(self._values)


class _LiveTrendReq:
    def build_payload(self, _payload, timeframe=None):
        return None

    def related_queries(self):
        return {"animals": {"top": _RelatedTop(["cat shirt trend", "dog mug trend"])}}

    def trending_searches(self, pn=None):
        return _TrendingRows(["live term 1", "live term 2"])


@pytest.mark.asyncio
async def test_fetch_trends_marks_live_source(monkeypatch):
    await init_db()
    monkeypatch.setattr(service, "TrendReq", _LiveTrendReq)

    trends = await service.fetch_trends(category="animals")

    assert trends
    assert all(item["trend_source"] == "live" for item in trends)


@pytest.mark.asyncio
async def test_fetch_trends_marks_fallback_source_when_pytrends_fails(monkeypatch):
    await init_db()

    class _FailingTrendReq:
        def __init__(self):
            raise RuntimeError("pytrends unavailable")

    monkeypatch.setattr(service, "TrendReq", _FailingTrendReq)

    trends = await service.fetch_trends(category="animals")

    assert trends
    assert all(item["trend_source"] == "fallback" for item in trends)
