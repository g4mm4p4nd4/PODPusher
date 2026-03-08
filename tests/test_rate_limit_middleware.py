import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from services.auth.service import create_session
from services.common.database import init_db
from services.common.rate_limit import PLAN_RATE_LIMITS, _limiter, register_rate_limiting


@pytest.fixture(autouse=True)
def _reset_limiter():
    _limiter._buckets.clear()
    yield
    _limiter._buckets.clear()


@pytest.mark.asyncio
async def test_rate_limit_uses_bearer_authenticated_user(monkeypatch):
    await init_db()
    token, _ = await create_session(77)

    app = FastAPI()
    register_rate_limiting(app)

    @app.get("/limited")
    async def limited():
        return {"ok": True}

    monkeypatch.setitem(PLAN_RATE_LIMITS, "free", 2)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.get("/limited", headers={"Authorization": f"Bearer {token}"})
        second = await client.get("/limited", headers={"Authorization": f"Bearer {token}"})
        third = await client.get("/limited", headers={"Authorization": f"Bearer {token}"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.json()["code"] == "RATE_LIMITED"
    assert third.headers["X-RateLimit-Limit"] == "2"
