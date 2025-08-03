"""Business logic for social media content generation."""
from __future__ import annotations

from typing import Dict

from packages.integrations.openai import generate_caption, generate_image


async def generate_post(prompt: str) -> Dict[str, str]:
    """Generate a caption and image for a social media post."""
    caption = await generate_caption(prompt)
    image_url = await generate_image(prompt)
    return {"caption": caption, "image_url": image_url}
