import os
import pytest
import httpx
from sqlmodel import select

from services.image_gen.service import generate_images
from services.common.database import init_db, get_session
from services.models import Idea, Image


@pytest.mark.asyncio
async def test_generate_images_persists(monkeypatch, tmp_path):
    await init_db()
    async with get_session() as session:
        idea = Idea(trend_id=0, description="test idea")
        session.add(idea)
        await session.commit()
        await session.refresh(idea)

    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("PROVIDER", "openai")
    monkeypatch.setenv("IMAGE_STORAGE", str(tmp_path))

    import openai

    def fake_create(**kwargs):
        return {"data": [{"url": "http://example.com/img.png"}]}

    async def fake_get(self, url):
        req = httpx.Request("GET", url)
        return httpx.Response(status_code=200, content=b"data", request=req)

    monkeypatch.setattr(openai.Image, "create", fake_create)
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    images = await generate_images(idea.id, "style")
    assert images[0]["id"] is not None
    assert os.path.exists(images[0]["url"])

    async with get_session() as session:
        res = await session.exec(select(Image))
        saved = res.first()
        assert saved is not None
