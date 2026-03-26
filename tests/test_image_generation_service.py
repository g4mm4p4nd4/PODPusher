import pytest

from services.common.database import get_session, init_db
from services.image_gen.service import delete_image, generate_image_for_idea, list_images
from services.models import Idea, Trend


async def _seed_idea(description: str = "cat t-shirt", category: str = "animals") -> int:
    async with get_session() as session:
        trend = Trend(term="cat", category=category)
        session.add(trend)
        await session.commit()
        await session.refresh(trend)

        idea = Idea(trend_id=trend.id, description=description)
        session.add(idea)
        await session.commit()
        await session.refresh(idea)
        return int(idea.id)


@pytest.mark.asyncio
async def test_generate_image_for_idea_persists_product(monkeypatch):
    await init_db()
    idea_id = await _seed_idea()

    async def fake_generate_image(prompt: str) -> str:
        assert "watercolor" in prompt
        return "https://example.com/generated.png"

    monkeypatch.setattr("services.image_gen.service.openai.generate_image", fake_generate_image)

    images = await generate_image_for_idea(idea_id, "watercolor")

    assert images
    assert images[0]["idea_id"] == idea_id
    assert images[0]["image_url"] == "https://example.com/generated.png"
    assert images[0]["provider"] == "openai"
    assert images[0]["generation_source"] == "openai"

    listed = await list_images(idea_id)
    assert listed
    assert listed[0]["id"] == images[0]["id"]


@pytest.mark.asyncio
async def test_generate_image_for_idea_supports_stub_provider_and_delete():
    await init_db()
    idea_id = await _seed_idea()

    images = await generate_image_for_idea(idea_id, "default", "stub")

    assert images
    assert images[0]["provider"] == "stub"
    assert images[0]["generation_source"] == "stub"

    listed = await list_images(idea_id)
    assert listed and listed[0]["id"] == images[0]["id"]

    deleted = await delete_image(images[0]["id"])
    assert deleted == {"status": "deleted"}
    assert await list_images(idea_id) == []
