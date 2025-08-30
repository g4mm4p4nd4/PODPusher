"""Business logic for social media content generation.

This module generates captions and simple placeholder images for
social posts using rule based templates and trending keywords.
"""

from __future__ import annotations

import base64
import json
import random
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

from PIL import Image, ImageDraw

TEMPLATE_DIR = Path(__file__).with_name("templates")
KEYWORDS_PATH = Path(__file__).with_name("trending_keywords.json")
PRODUCT_PATH = Path(__file__).with_name("sample_products.json")


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def _load_templates(language: str) -> Dict[str, str]:
    path = TEMPLATE_DIR / f"{language}.json"
    if not path.exists():
        path = TEMPLATE_DIR / "en.json"
    return _load_json(path)


KEYWORDS = _load_json(KEYWORDS_PATH)
PRODUCTS = _load_json(PRODUCT_PATH)


def _choose_keyword(language: str, product_type: str) -> str:
    lang_data = KEYWORDS.get(language, KEYWORDS["en"])
    keywords = lang_data.get(product_type, lang_data.get("default", []))
    return random.choice(keywords) if keywords else ""  # pragma: no cover


def _render_image(text: str) -> str:
    """Return base64 encoded PNG with the provided text."""
    img = Image.new("RGB", (400, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 180), text[:30], fill=(0, 0, 0))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _get_product(product_id: int) -> Dict[str, Any] | None:
    return PRODUCTS.get(str(product_id))


async def generate_post(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a caption and optional image for a social media post."""
    if product_id := data.get("product_id"):
        product = _get_product(product_id)
        if product:
            data = {**product, **{k: v for k, v in data.items() if v is not None}}

    language = data.get("language", "en")
    product_type = data.get("product_type", "default")
    templates = _load_templates(language)
    template = templates.get(product_type, templates["default"])
    keyword = _choose_keyword(language, product_type)
    tags = ", ".join(data.get("tags", []))
    caption = template.format(
        title=data.get("title", ""),
        description=data.get("description", ""),
        tags=tags,
        keyword=keyword,
    )
    image = None
    if data.get("include_image", True):
        image = _render_image(data.get("title", ""))
    return {"caption": caption, "image": image}
