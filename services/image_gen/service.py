from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, List, Union

from sqlmodel import select

from packages.integrations import openai

from ..common.database import get_session
from ..models import Idea, Product, Trend

PLACEHOLDER_IMAGE_URL = "http://example.com/image.png"
ImageProvider = Callable[[str], Awaitable[str]]


def _classify_image_source(url: str) -> str:
    """Classify where an image URL likely came from."""
    if url.strip() == PLACEHOLDER_IMAGE_URL:
        return "stub"
    return "openai"


async def _stub_generate_image(_prompt: str) -> str:
    return PLACEHOLDER_IMAGE_URL


def _provider_name(provider_override: str | None = None) -> str:
    provider = (provider_override or "openai").strip().lower()
    if provider in {"", "default"}:
        return "openai"
    if provider in {"openai", "stub"}:
        return provider
    return "openai"


def _provider_for(provider_override: str | None = None) -> ImageProvider:
    provider = _provider_name(provider_override)
    if provider == "stub":
        return _stub_generate_image
    return openai.generate_image


def _serialize_product_image(
    product: Product,
    *,
    category: str | None,
    provider: str,
    generation_source: str,
) -> Dict[str, Any]:
    return {
        "id": product.id,
        "idea_id": product.idea_id,
        "image_url": product.image_url,
        "url": product.image_url,
        "category": category,
        "provider": provider,
        "generation_source": generation_source,
    }


async def _create_idea_record(description: str, category: str) -> int:
    async with get_session() as session:
        trend = Trend(term=description, category=category)
        session.add(trend)
        await session.commit()
        await session.refresh(trend)

        idea_rec = Idea(trend_id=trend.id, description=description)
        session.add(idea_rec)
        await session.commit()
        await session.refresh(idea_rec)
        return int(idea_rec.id)


async def _idea_category(idea_id: int) -> str | None:
    async with get_session() as session:
        idea = await session.get(Idea, idea_id)
        if not idea:
            return None
        trend = await session.get(Trend, idea.trend_id)
        if not trend:
            return None
        return trend.category


async def generate_image_for_idea(
    idea_id: int,
    style: str = "default",
    provider_override: str | None = None,
    category: str | None = None,
) -> List[Dict[str, Any]]:
    provider = _provider_name(provider_override)
    generator = _provider_for(provider_override)

    async with get_session() as session:
        idea = await session.get(Idea, idea_id)
        if not idea:
            return []
        resolved_category = category
        if resolved_category is None:
            trend = await session.get(Trend, idea.trend_id)
            resolved_category = trend.category if trend else None

    style_name = (style or "default").strip()
    prompt = idea.description if style_name == "default" else f"{idea.description} in {style_name} style"

    try:
        image_url = await generator(prompt)
        generation_source = "stub" if provider == "stub" else _classify_image_source(image_url)
    except Exception:
        image_url = PLACEHOLDER_IMAGE_URL
        generation_source = "fallback"

    async with get_session() as session:
        product = Product(idea_id=idea_id, image_url=image_url)
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return [
            _serialize_product_image(
                product,
                category=resolved_category,
                provider=provider,
                generation_source=generation_source,
            )
        ]


async def list_images(idea_id: int) -> List[Dict[str, Any]]:
    category = await _idea_category(idea_id)
    async with get_session() as session:
        result = await session.exec(
            select(Product).where(Product.idea_id == idea_id).order_by(Product.created_at.desc())
        )
        products = result.all()
    return [
        _serialize_product_image(
            product,
            category=category,
            provider=_classify_image_source(product.image_url),
            generation_source=_classify_image_source(product.image_url),
        )
        for product in products
    ]


async def delete_image(image_id: int) -> Dict[str, str]:
    async with get_session() as session:
        product = await session.get(Product, image_id)
        if not product:
            return {"status": "not_found"}
        await session.delete(product)
        await session.commit()
        return {"status": "deleted"}


async def generate_images(ideas: List[Union[Dict, str]]) -> List[Dict]:
    normalized: List[Dict[str, Any]] = []
    for idea in ideas:
        if isinstance(idea, dict):
            normalized.append(
                {
                    "id": idea.get("id"),
                    "description": (
                        idea.get("description")
                        or idea.get("prompt")
                        or idea.get("term")
                    ),
                    "category": (idea.get("category") or "general").lower(),
                    "style": idea.get("style") or "default",
                    "provider_override": idea.get("provider_override"),
                }
            )
        else:
            normalized.append(
                {
                    "id": None,
                    "description": str(idea),
                    "category": "general",
                    "style": "default",
                    "provider_override": None,
                }
            )

    products: List[Dict] = []
    for item in normalized:
        idea_id = item.get("id")
        if idea_id is None:
            idea_id = await _create_idea_record(
                description=item["description"],
                category=item.get("category", "general"),
            )
            item["id"] = idea_id

        generated = await generate_image_for_idea(
            idea_id=int(idea_id),
            style=item.get("style", "default"),
            provider_override=item.get("provider_override"),
            category=item.get("category"),
        )
        products.extend(generated)
    return products
