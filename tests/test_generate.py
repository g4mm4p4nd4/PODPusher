import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import httpx

from services.gateway.main import app


@pytest.mark.asyncio
async def test_generate_pipeline():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/generate")
    assert response.status_code == 200
    data = response.json()
    for key in ("trends", "ideas", "images", "product", "listing"):
        assert key in data
