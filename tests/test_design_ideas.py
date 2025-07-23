import pytest
from httpx import AsyncClient, ASGITransport
from services.gateway.api import app as gateway_app


@pytest.mark.asyncio
async def test_design_ideas_endpoint():
    transport = ASGITransport(app=gateway_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/design-ideas")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 5
        found = False
        for cat in data:
            ideas = cat.get("ideas", [])
            if any("acrylic" in i.lower() or "blanket" in i.lower() for i in ideas):
                found = True
        assert found

        resp = await client.get("/design-ideas", params={"category": "animals_pets"})
        assert resp.status_code == 200
        filtered = resp.json()
        assert len(filtered) == 1
        assert filtered[0]["name"] == "animals_pets"
