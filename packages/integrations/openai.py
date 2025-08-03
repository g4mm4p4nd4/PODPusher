"""OpenAI integration helpers.

These functions wrap calls to the OpenAI API.  If the
``OPENAI_API_KEY`` environment variable is not set or
``OPENAI_USE_STUB`` is truthy, deterministic stub responses are
returned instead.  Simple retry logic handles rate limits (HTTP 429)
with exponential backoff.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

API_BASE = "https://api.openai.com/v1"
API_KEY = os.getenv("OPENAI_API_KEY")
USE_STUB = os.getenv("OPENAI_USE_STUB", "1").lower() in {"1", "true", "yes"}

HEADERS = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}


async def _post(path: str, payload: dict[str, Any]) -> Any:
    """POST helper with naive exponential backoff."""
    if USE_STUB or not API_KEY:
        raise RuntimeError("Real API calls disabled")

    async with httpx.AsyncClient(timeout=10) as client:
        for attempt in range(3):
            resp = await client.post(f"{API_BASE}{path}", headers=HEADERS, json=payload)
            if resp.status_code == 429:
                await asyncio.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            return resp.json()
    raise RuntimeError("OpenAI request failed after retries")


async def generate_caption(prompt: str) -> str:
    """Return a marketing caption for a given prompt."""
    if USE_STUB or not API_KEY:
        return f"Caption for: {prompt}"

    data = await _post(
        "/chat/completions",
        {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    return data["choices"][0]["message"]["content"].strip()


async def generate_image(prompt: str) -> str:
    """Return a URL to an image generated from the prompt."""
    if USE_STUB or not API_KEY:
        return "http://example.com/image.png"

    data = await _post(
        "/images/generations",
        {"model": "gpt-image-1", "prompt": prompt, "size": "512x512"},
    )
    return data["data"][0]["url"]


async def suggest_tags(text: str) -> list[str]:
    """Suggest up to 13 tags for the given text."""
    if USE_STUB or not API_KEY:
        words = [w.strip(".,!?:;\"'()[]{}").lower() for w in text.split()]
        stop = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "of",
            "in",
            "with",
            "to",
            "for",
            "on",
            "at",
            "by",
        }
        tags: list[str] = []
        for w in words:
            if w and w not in stop and w not in tags:
                tags.append(w)
            if len(tags) >= 13:
                break
        return tags

    data = await _post(
        "/chat/completions",
        {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Suggest up to 13 concise Etsy tags for the following listing: "
                        f"{text}. Return the tags separated by commas."
                    ),
                }
            ],
        },
    )
    content = data["choices"][0]["message"]["content"]
    return [t.strip() for t in content.split(",") if t.strip()][:13]
