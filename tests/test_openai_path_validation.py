import pytest

from services.common.database import init_db
from services.ideation.service import generate_ideas
from services.image_gen.service import generate_images


@pytest.mark.asyncio
async def test_generate_ideas_marks_stub_source(monkeypatch):
    await init_db()

    async def fake_generate_brief(_prompt: str) -> str:
        return "Idea brief: cat t-shirt"

    monkeypatch.setattr("services.ideation.service.openai.generate_brief", fake_generate_brief)

    ideas = await generate_ideas([{"term": "cat", "category": "animals"}])

    assert ideas
    assert ideas[0]["generation_source"] == "stub"
    assert ideas[0]["implementation_status"] == "needs_implementation"
    assert ideas[0]["requires_attention"] is True


@pytest.mark.asyncio
async def test_generate_ideas_marks_fallback_source_on_exception(monkeypatch):
    await init_db()

    async def failing_generate_brief(_prompt: str) -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr("services.ideation.service.openai.generate_brief", failing_generate_brief)

    ideas = await generate_ideas([{"term": "cat", "category": "animals"}])

    assert ideas
    assert ideas[0]["generation_source"] == "fallback"
    assert ideas[0]["implementation_status"] == "needs_implementation"
    assert ideas[0]["requires_attention"] is True


@pytest.mark.asyncio
async def test_generate_images_marks_stub_source(monkeypatch):
    await init_db()

    async def fake_generate_image(_prompt: str) -> str:
        return "http://example.com/image.png"

    monkeypatch.setattr("services.image_gen.service.openai.generate_image", fake_generate_image)

    images = await generate_images([{"description": "cat t-shirt", "category": "animals"}])

    assert images
    assert images[0]["generation_source"] == "stub"
    assert images[0]["implementation_status"] == "needs_implementation"
    assert images[0]["requires_attention"] is True


@pytest.mark.asyncio
async def test_generate_images_marks_fallback_source_on_exception(monkeypatch):
    await init_db()

    async def failing_generate_image(_prompt: str) -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr("services.image_gen.service.openai.generate_image", failing_generate_image)

    images = await generate_images([{"description": "cat t-shirt", "category": "animals"}])

    assert images
    assert images[0]["generation_source"] == "fallback"
    assert images[0]["implementation_status"] == "needs_implementation"
    assert images[0]["requires_attention"] is True
