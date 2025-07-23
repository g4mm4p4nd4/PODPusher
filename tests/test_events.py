import pytest
from httpx import AsyncClient, ASGITransport
from services.trend_scraper.api import app as trends_app
from datetime import datetime


@pytest.mark.asyncio
async def test_events_endpoint():
    transport = ASGITransport(app=trends_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/events/may")
        assert resp.status_code == 200
        data = resp.json()
        assert data["month"].lower() == "may"
        assert isinstance(data["events"], list)

        current = datetime.utcnow().strftime("%B").lower()
        resp = await client.get(f"/events/{current}")
        assert resp.status_code == 200
