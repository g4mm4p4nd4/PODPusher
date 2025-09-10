from __future__ import annotations

"""Google Gemini image API integration."""

import logging
import os
from typing import Dict

import httpx

logger = logging.getLogger(__name__)
API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _generate_mockup_real(api_key: str, prompt: str) -> str:
    params = {"key": api_key}
    payload: Dict[str, str] = {"prompt": prompt}
    try:
        resp = httpx.post(
            f"{API_BASE}/models/gemini-pro-vision:generateImage",
            params=params,
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        # Simplified extraction assuming first image URL in response
        return data.get("data", [{}])[0].get("url", "")
    except httpx.HTTPError as exc:
        logger.error("Gemini API error: %s", exc)
        raise


def _generate_mockup_stub(prompt: str) -> str:
    logger.info("GEMINI_API_KEY missing; returning stub image")
    return "http://example.com/mockup.png"


def generate_mockup(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _generate_mockup_stub(prompt)
    return _generate_mockup_real(api_key, prompt)
