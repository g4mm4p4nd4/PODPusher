"""OpenAI integration helpers using the official 1.x SDK.

These helpers centralise access to chat, image, and tag suggestions. When
OPENAI_USE_STUB is truthy (the default in tests) or the API key is missing,
stub responses are returned so the rest of the pipeline can run without
external calls.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Awaitable, Callable, Optional

from openai import APIError, APITimeoutError, AsyncOpenAI, RateLimitError

API_KEY = os.getenv("OPENAI_API_KEY")
USE_STUB = os.getenv("OPENAI_USE_STUB", "1").lower() in {"1", "true", "yes"}
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
IMAGE_SIZE = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")
MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
BACKOFF_SECONDS = float(os.getenv("OPENAI_BACKOFF_SECONDS", "1.0"))
BACKOFF_MULTIPLIER = float(os.getenv("OPENAI_BACKOFF_MULTIPLIER", "2.0"))

TAG_STRIP_CHARS = ".,!?:;\"'()[]{}"

_client: Optional[AsyncOpenAI] = None


def _create_client() -> AsyncOpenAI:
    if not API_KEY:
        raise RuntimeError("OpenAI API key missing while stub mode disabled")
    kwargs: dict[str, Any] = {"api_key": API_KEY}
    org = os.getenv("OPENAI_ORG")
    if org:
        kwargs["organization"] = org
    project = os.getenv("OPENAI_PROJECT")
    if project:
        kwargs["project"] = project
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        kwargs["base_url"] = base_url
    return AsyncOpenAI(**kwargs)


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = _create_client()
    return _client


def _is_retryable(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if status is None:
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None)
    if status in {401, 403, 400}:
        return False
    if status in {408, 409, 425, 429, 500, 502, 503, 504}:
        return True
    return isinstance(exc, (RateLimitError, APITimeoutError))


async def _with_retry(fn: Callable[[], Awaitable[Any]]) -> Any:
    delay = BACKOFF_SECONDS
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await fn()
        except (RateLimitError, APITimeoutError, APIError) as exc:  # pragma: no cover - error path
            last_exc = exc
            if attempt >= MAX_RETRIES or not _is_retryable(exc):
                raise
        except Exception as exc:  # pragma: no cover - defensive guard
            last_exc = exc
            raise
        await asyncio.sleep(max(delay, 0.1))
        delay *= BACKOFF_MULTIPLIER
    if last_exc is not None:  # pragma: no cover - should not happen
        raise last_exc
    raise RuntimeError("OpenAI call failed without raising an error")


def _coerce_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") if item.get("type") == "text" else None
                if text:
                    parts.append(str(text))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content)


async def generate_caption(prompt: str) -> str:
    if USE_STUB or not API_KEY:
        return f"Caption for: {prompt}"

    async def _call() -> Any:
        client = _get_client()
        return await client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

    response = await _with_retry(_call)
    choice = response.choices[0]
    message = getattr(choice, "message", None) or choice.get("message")  # type: ignore[arg-type]
    content = _coerce_text(getattr(message, "content", None) if message else None)
    return content.strip()


async def generate_brief(prompt: str) -> str:
    if USE_STUB or not API_KEY:
        return f"Idea brief: {prompt}"

    async def _call() -> Any:
        client = _get_client()
        return await client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": "You craft concise e-commerce product briefs."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )

    response = await _with_retry(_call)
    choice = response.choices[0]
    message = getattr(choice, "message", None) or choice.get("message")  # type: ignore[arg-type]
    content = _coerce_text(getattr(message, "content", None) if message else None)
    return content.strip()


async def generate_image(prompt: str) -> str:
    if USE_STUB or not API_KEY:
        return "http://example.com/image.png"

    async def _call() -> Any:
        client = _get_client()
        return await client.images.generate(
            model=IMAGE_MODEL,
            prompt=prompt,
            size=IMAGE_SIZE,
            response_format="url",
        )

    response = await _with_retry(_call)
    data = response.data[0]
    url = getattr(data, "url", None)
    if url is None and isinstance(data, dict):
        url = data.get("url")
    if not url:
        raise RuntimeError("OpenAI image response missing URL")
    return str(url)


async def suggest_tags(text: str) -> list[str]:
    if USE_STUB or not API_KEY:
        words = [w.strip(TAG_STRIP_CHARS).lower() for w in text.split()]
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

    async def _call() -> Any:
        client = _get_client()
        return await client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Suggest up to 13 concise Etsy tags for the following listing: "
                        f"{text}. Return the tags separated by commas."
                    ),
                }
            ],
            temperature=0.2,
        )

    response = await _with_retry(_call)
    choice = response.choices[0]
    message = getattr(choice, "message", None) or choice.get("message")  # type: ignore[arg-type]
    content = _coerce_text(getattr(message, "content", None) if message else None)
    return [t.strip() for t in content.split(",") if t.strip()][:13]
