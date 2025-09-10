import base64
import os

import openai
import pytest

from services.image_gen.service import generate_images
from services.models import Idea, Image
from services.common.database import init_db, get_session
from sqlmodel import select


@pytest.mark.asyncio
async def test_generate_images_openai(monkeypatch, tmp_path):
    os.environ['OPENAI_API_KEY'] = 'x'
    os.environ['PROVIDER'] = 'openai'
    os.environ['IMAGE_DIR'] = str(tmp_path)

    fake = {"data": [{'b64_json': base64.b64encode(b'test').decode()}]}
    monkeypatch.setattr(openai.Image, 'create', lambda **kwargs: fake)

    await init_db()
    async with get_session() as session:
        idea = Idea(trend_id=0, description='idea')
        session.add(idea)
        await session.commit()
        await session.refresh(idea)
        idea_id = idea.id
    urls = await generate_images(idea_id, 'style')
    assert urls
    assert os.path.exists(urls[0])
    async with get_session() as session:
        result = await session.exec(select(Image))
        img = result.first()
        assert img.provider == 'openai'


@pytest.mark.asyncio
async def test_generate_images_gemini(monkeypatch, tmp_path):
    os.environ['GEMINI_API_KEY'] = 'y'
    os.environ['PROVIDER'] = 'gemini'
    os.environ['IMAGE_DIR'] = str(tmp_path)

    class DummyResponse:
        def json(self):
            return {'data': [{'b64_json': base64.b64encode(b'gm').decode()}]}
        def raise_for_status(self):
            return None

    async def fake_post(self, url, json):
        return DummyResponse()

    monkeypatch.setattr('httpx.AsyncClient.post', fake_post)

    await init_db()
    async with get_session() as session:
        idea = Idea(trend_id=0, description='idea')
        session.add(idea)
        await session.commit()
        await session.refresh(idea)
        idea_id = idea.id
    urls = await generate_images(idea_id, 'style')
    assert urls
    assert os.path.exists(urls[0])
    async with get_session() as session:
        result = await session.exec(select(Image))
        img = result.first()
        assert img.provider == 'gemini'
