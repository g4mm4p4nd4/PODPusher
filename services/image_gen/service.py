import base64
import logging
import os
from uuid import uuid4
from typing import List, Optional

import httpx
from sqlmodel import select

from ..models import Idea, Image, Product
from ..common.database import get_session

logger = logging.getLogger(__name__)

PLACEHOLDER_URL = "http://example.com/placeholder.png"


async def _save_image(image_bytes: bytes) -> str:
    bucket = os.getenv("S3_BUCKET")
    filename = f"{uuid4().hex}.png"
    if bucket:
        try:
            import boto3

            s3 = boto3.client("s3")
            s3.put_object(Bucket=bucket, Key=filename, Body=image_bytes, ContentType="image/png")
            return f"https://{bucket}.s3.amazonaws.com/{filename}"
        except Exception:  # pragma: no cover - best effort
            logger.exception("Failed to upload image to S3; falling back to local storage")
    storage_dir = os.getenv("IMAGE_DIR", "/data/images")
    os.makedirs(storage_dir, exist_ok=True)
    path = os.path.join(storage_dir, filename)
    with open(path, "wb") as f:
        f.write(image_bytes)
    return path


def _get_provider(override: Optional[str]) -> str:
    return (override or os.getenv("PROVIDER") or "openai").lower()


def _openai_image(prompt: str) -> bytes:
    import openai

    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Image.create(
        prompt=prompt,
        size="1024x1024",
        response_format="b64_json",
    )
    b64 = response["data"][0]["b64_json"]
    return base64.b64decode(b64)


async def _gemini_image(prompt: str, model: Optional[str] = None) -> bytes:
    model = model or os.getenv("GEMINI_MODEL", "models/gemini-pro-vision")
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateImage?key={api_key}"
    payload = {"prompt": {"text": prompt}, "size": {"width": 512, "height": 512}}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        b64 = data["data"][0]["b64_json"]
        return base64.b64decode(b64)


async def generate_images(idea_id: int, style: str, provider_override: Optional[str] = None) -> List[str]:
    provider = _get_provider(provider_override)
    async with get_session() as session:
        idea = await session.get(Idea, idea_id)
        if not idea:
            logger.error("Idea %s not found", idea_id)
            return [PLACEHOLDER_URL]
    prompt = f"{idea.description} in {style} style"
    try:
        if provider == "gemini":
            image_bytes = await _gemini_image(prompt)
        else:
            image_bytes = _openai_image(prompt)
        url = await _save_image(image_bytes)
        async with get_session() as session:
            image = Image(idea_id=idea_id, provider=provider, url=url)
            session.add(image)
            await session.commit()
            await session.refresh(image)
            product = Product(idea_id=idea_id, image_url=url)
            session.add(product)
            await session.commit()
        return [url]
    except Exception:  # pragma: no cover - error path
        logger.exception("Image generation failed")
        return [PLACEHOLDER_URL]


async def list_images(idea_id: int) -> List[dict]:
    async with get_session() as session:
        result = await session.exec(select(Image).where(Image.idea_id == idea_id))
        return [img.model_dump() for img in result.all()]


async def delete_image(image_id: int) -> dict:
    async with get_session() as session:
        image = await session.get(Image, image_id)
        if image:
            await session.delete(image)
            await session.commit()
            return {"status": "deleted"}
    return {"status": "not_found"}
