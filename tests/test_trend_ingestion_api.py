import pytest
from httpx import AsyncClient, ASGITransport

from services.gateway.api import app as gateway_app
from services.common.database import init_db, get_session
from services.models import TrendSignal


@pytest.mark.asyncio
async def test_live_trends_endpoint():
    await init_db()
    async with get_session() as session:
        session.add(
            TrendSignal(source="tiktok", keyword="funny cat", engagement_score=5, category="animals")
        )
        session.add(
            TrendSignal(source="twitter", keyword="climate", engagement_score=3, category="activism")
        )
        await session.commit()

    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/trends/live")
        assert resp.status_code == 200
        data = resp.json()
        assert "animals" in data
        assert data["animals"][0]["keyword"] == "funny cat"

        resp = await client.get("/api/trends/live", params={"category": "activism"})
        assert resp.status_code == 200
        filtered = resp.json()
        assert list(filtered.keys()) == ["activism"]


@pytest.mark.asyncio
async def test_refresh_endpoint(monkeypatch):
    await init_db()

    async def fake_refresh():
        async with get_session() as session:
            session.add(
                TrendSignal(
                    source="etsy",
                    keyword="handmade",
                    engagement_score=1,
                    category="other",
                )
            )
            await session.commit()

    monkeypatch.setattr("services.gateway.api.refresh_trends", fake_refresh)

    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/trends/refresh")
        assert resp.status_code == 200

        resp = await client.get("/api/trends/live")
        data = resp.json()
        assert "other" in data
