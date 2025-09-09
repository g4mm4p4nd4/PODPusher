import asyncio
import logging
import os
import uuid
from typing import List, Dict, Optional

import httpx

from ..models import Image, Idea
from ..common.database import get_session
from sqlmodel import select

logger = logging.getLogger(__name__)

PLACEHOLDER_URL = "https://placehold.co/1024x1024?text=Image+Unavailable"
STORAGE_DIR = os.getenv("IMAGE_STORAGE", "/data/images")
DEFAULT_PROVIDER = os.getenv("PROVIDER", "openai").lower()


async def _download_and_store(url: str) -> str:
    os.makedirs(STORAGE_DIR, exist_ok=True)
    filename = f"{uuid.uuid4()}.png"
    path = os.path.join(STORAGE_DIR, filename)
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        with open(path, "wb") as f:
            f.write(resp.content)
    return path


async def _generate_openai(prompt: str) -> str:
    import openai

    openai.api_key = os.getenv("OPENAI_API_KEY")

    def _call() -> Dict:
        return openai.Image.create(prompt=prompt, n=1, size="1024x1024")

    response = await asyncio.to_thread(_call)
    return response["data"][0]["url"]


async def _generate_gemini(prompt: str, model: Optional[str] = None) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    model = model or os.getenv("GEMINI_MODEL", "models/gemini-pro-vision")
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateImage"
    params = {"key": api_key}
    payload = {"prompt": {"text": prompt}, "size": "512x512"}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(endpoint, params=params, json=payload)
    if resp.status_code == 429:
        logger.warning("Gemini rate limit hit: %s", resp.text)
        raise RuntimeError("rate limited")
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0]["url"]


async def generate_images(
    idea_id: int,
    style: str,
    provider_override: Optional[str] = None,
    model_version: Optional[str] = None,
) -> List[Dict]:
    provider = (provider_override or DEFAULT_PROVIDER).lower()
    async with get_session() as session:
        idea = await session.get(Idea, idea_id)
        if not idea:
            raise ValueError("idea not found")
    prompt = f"{style} {idea.description}".strip()
    try:
        if provider == "gemini":
            url = await _generate_gemini(prompt, model_version)
        else:
            url = await _generate_openai(prompt)
        stored = await _download_and_store(url)
        async with get_session() as session:
            image = Image(idea_id=idea_id, provider=provider, url=stored)
            session.add(image)
            await session.commit()
            await session.refresh(image)
        return [{"id": image.id, "url": image.url}]
    except Exception as exc:
        logger.error("Image generation failed: %s", exc)
        return [{"id": None, "url": PLACEHOLDER_URL}]


async def list_images(idea_id: int) -> List[Dict]:
    async with get_session() as session:
        result = await session.exec(select(Image).where(Image.idea_id == idea_id))
        images = result.all()
        return [{"id": img.id, "url": img.url, "provider": img.provider} for img in images]


async def delete_image(image_id: int) -> bool:
    async with get_session() as session:
        image = await session.get(Image, image_id)
        if not image:
            return False
        await session.delete(image)
        await session.commit()
    try:
        if os.path.exists(image.url):
            os.remove(image.url)
    except OSError:
        pass
    return True
