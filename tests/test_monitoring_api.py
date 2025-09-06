import pytest
from httpx import AsyncClient, ASGITransport

from services.analytics.api import app as analytics_app
from services.common.database import init_db


@pytest.mark.asyncio
async def test_event_list_endpoint():
    await init_db()
    transport = ASGITransport(app=analytics_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/analytics/events", json={"event_type": "click", "path": "/a"})
        await client.post("/analytics/events", json={"event_type": "view", "path": "/b"})
        resp = await client.get("/analytics/events", params={"event_type": "click"})
        assert resp.status_code == 200
        events = resp.json()
        assert len(events) == 1
        assert events[0]["path"] == "/a"
