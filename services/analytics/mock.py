"""Mock analytics keyword data for API responses."""
from __future__ import annotations

from typing import List, Dict

_RAW_KEYWORDS: List[Dict[str, int | str]] = [
    {"term": "print on demand shirts", "clicks": 230},
    {"term": "custom mug", "clicks": 175},
    {"term": "etsy seo tips", "clicks": 98},
    {"term": "holiday sweater", "clicks": 142},
    {"term": "pet portrait", "clicks": 260},
    {"term": "minimalist poster", "clicks": 118},
    {"term": "trend report", "clicks": 87},
    {"term": "bulk order", "clicks": 64},
    {"term": "wedding invite", "clicks": 156},
    {"term": "summer tote", "clicks": 121},
    {"term": "sports jersey", "clicks": 111},
    {"term": "boho decor", "clicks": 134},
]

MOCK_KEYWORDS: List[Dict[str, int | str]] = sorted(
    _RAW_KEYWORDS, key=lambda item: item["clicks"], reverse=True
)[:10]

__all__ = ["MOCK_KEYWORDS"]
