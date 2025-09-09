import asyncio
import logging
import os
import uuid
from typing import List, Optional

import httpx

from ..models import Idea, Image, Product
from ..common.database import get_session

logger = logging.getLogger(__name__)

PLACEHOLDER_URL = "https://placehold.co/1024x1024?text=Image"


async def _store_image(content: bytes, filename: str) -> str:
    bucket = os.getenv("S3_BUCKET")
    if bucket:
        try:
            import boto3

            s3 = boto3.client("s3")
            s3.put_object(Bucket=bucket, Key=filename, Body=content)
            return f"s3://{bucket}/{filename}"
        except Exception:
            logger.exception("Failed to upload to S3")
    storage_dir = os.getenv("IMAGE_STORAGE", "/data/images")
    os.makedirs(storage_dir, exist_ok=True)
    path = os.path.join(storage_dir, filename)
    with open(path, "wb") as f:
        f.write(content)
    return path


async def _download_and_store(url: str) -> str:
    filename = f"{uuid.uuid4()}.png"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
    return await _store_image(resp.content, filename)


async def generate_images(
    idea_id: int, style: str, provider_override: Optional[str] = None
) -> List[str]:
    provider = (provider_override or os.getenv("PROVIDER", "openai")).lower()
    async with get_session() as session:
        idea = await session.get(Idea, idea_id)
    if not idea:
        return [PLACEHOLDER_URL]
    prompt = f"{style} {idea.description}".strip()
    url = PLACEHOLDER_URL
    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-pro-vision")
        if api_key:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateImage",
                        params={"key": api_key},
                        json={"prompt": {"text": prompt}, "size": "512x512"},
                    )
                    if resp.status_code == 429:
                        logger.error("Gemini rate limited")
                    resp.raise_for_status()
                    url = resp.json().get("data", [{}])[0].get("url", PLACEHOLDER_URL)
            except Exception:
                logger.exception("Gemini image generation failed")
        else:
            logger.error("GEMINI_API_KEY missing")
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                import openai

                openai.api_key = api_key
                response = await asyncio.to_thread(
                    openai.Image.create, prompt=prompt, n=1, size="1024x1024"
                )
                url = response["data"][0]["url"]
            except Exception:
                logger.exception("OpenAI image generation failed")
        else:
            logger.error("OPENAI_API_KEY missing")
    if url == PLACEHOLDER_URL:
        stored_url = PLACEHOLDER_URL
    else:
        try:
            stored_url = await _download_and_store(url)
        except Exception:
            logger.exception("Failed to store image")
            stored_url = url
    async with get_session() as session:
        image = Image(idea_id=idea_id, provider=provider, url=stored_url)
        session.add(image)
        session.add(Product(idea_id=idea_id, image_url=stored_url))
        await session.commit()
    return [stored_url]
