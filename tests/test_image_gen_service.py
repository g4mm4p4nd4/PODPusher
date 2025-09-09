import os
from sqlmodel import select
import pytest

from services.image_gen.service import generate_images
from services.models import Idea, Image
from services.common.database import init_db, get_session


@pytest.mark.asyncio
async def test_generate_images_openai(monkeypatch, tmp_path):
    await init_db()
    os.environ["OPENAI_API_KEY"] = "test"
    os.environ["PROVIDER"] = "openai"
    monkeypatch.setenv("IMAGE_STORAGE", str(tmp_path))

    def fake_create(**_):
        return {"data": [{"url": "http://example.com/img.png"}]}

    async def fake_get(url):
        class Resp:
            status_code = 200
            content = b"img"

            def raise_for_status(self):
                pass

        return Resp()

    import openai
    monkeypatch.setattr(openai.Image, "create", fake_create)
    monkeypatch.setattr("httpx.AsyncClient.get", lambda self, url: fake_get(url))

    async with get_session() as session:
        idea = Idea(trend_id=1, description="desc")
        session.add(idea)
        await session.commit()
        await session.refresh(idea)
    urls = await generate_images(idea.id, "style")
    assert urls
    stored = urls[0]
    assert stored.startswith(str(tmp_path))
    async with get_session() as session:
        result = await session.exec(select(Image))
        images = result.all()
        assert images and images[0].provider == "openai"


@pytest.mark.asyncio
async def test_provider_override(monkeypatch, tmp_path):
    await init_db()
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ["GEMINI_API_KEY"] = "gtest"
    monkeypatch.setenv("IMAGE_STORAGE", str(tmp_path))

    async def fake_post(*args, **kwargs):
        class Resp:
            status_code = 200
            content = b"img"

            def json(self):
                return {"data": [{"url": "http://example.com/g.png"}]}

            def raise_for_status(self):
                pass

        return Resp()

    monkeypatch.setattr("httpx.AsyncClient.post", fake_post)
    monkeypatch.setattr("httpx.AsyncClient.get", lambda self, url: fake_post())

    async with get_session() as session:
        idea = Idea(trend_id=1, description="desc")
        session.add(idea)
        await session.commit()
        await session.refresh(idea)
    urls = await generate_images(idea.id, "style", provider_override="gemini")
    assert urls
    async with get_session() as session:
        result = await session.exec(select(Image))
        images = result.all()
        assert images and images[0].provider == "gemini"
