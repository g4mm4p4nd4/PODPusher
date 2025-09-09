import os
import pytest
from httpx import AsyncClient, ASGITransport
from services.image_gen.api import app as image_app
from services.common.database import init_db, get_session
from services.models import User, Idea


@pytest.mark.asyncio
async def test_quota_enforcement():
    await init_db()
    async with get_session() as session:
        idea = Idea(trend_id=0, description="idea")
        user = User(id=1)
        session.add(idea)
        session.add(user)
        await session.commit()
        await session.refresh(idea)
    transport = ASGITransport(app=image_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for i in range(21):
            resp = await client.post(
                "/generate",
                json={"idea_id": idea.id, "style": "s"},
                headers={"X-User-Id": "1"},
            )
            if i < 20:
                assert resp.status_code == 200
            else:
                assert resp.status_code == 403
