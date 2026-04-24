"""ScrapeGraphAI integration for public trend extraction.

The adapter is optional at import time so unit tests and non-Docker local
commands can run before the Docker image installs scrapegraphai.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List

from .sources import SourceConfig

logger = logging.getLogger(__name__)

PUBLIC_ONLY_ENV_BLOCKLIST = (
    "TREND_INGESTION_COOKIE_FILE",
    "TREND_INGESTION_SESSION_FILE",
    "TREND_INGESTION_LOGIN_URL",
    "TREND_INGESTION_USERNAME",
    "TREND_INGESTION_PASSWORD",
)

SCRAPEGRAPH_MODEL = os.getenv("SCRAPEGRAPH_MODEL", "ollama/llama3.2")
SCRAPEGRAPH_MODEL_TOKENS = int(os.getenv("SCRAPEGRAPH_MODEL_TOKENS", "8192"))
SCRAPEGRAPH_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
SCRAPEGRAPH_ENABLED = os.getenv("TREND_INGESTION_SCRAPEGRAPH", "1").lower() in {
    "1",
    "true",
    "yes",
    "on",
}


class PublicOnlyConfigError(RuntimeError):
    """Raised when a credential/session based scraper setting is present."""


class ScrapeGraphUnavailable(RuntimeError):
    """Raised when ScrapeGraphAI cannot be used in this environment."""


def validate_public_only_config() -> None:
    configured = [name for name in PUBLIC_ONLY_ENV_BLOCKLIST if os.getenv(name)]
    if configured:
        raise PublicOnlyConfigError(
            "Trend ingestion public-only mode rejects credential/session settings: "
            + ", ".join(configured)
        )


def _graph_config() -> Dict[str, Any]:
    llm_config: Dict[str, Any] = {
        "model": SCRAPEGRAPH_MODEL,
        "model_tokens": SCRAPEGRAPH_MODEL_TOKENS,
        "format": "json",
    }
    if SCRAPEGRAPH_MODEL.startswith("ollama/") and SCRAPEGRAPH_OLLAMA_BASE_URL:
        llm_config["base_url"] = SCRAPEGRAPH_OLLAMA_BASE_URL
    return {
        "llm": llm_config,
        "verbose": False,
        "headless": True,
    }


def _prompt_for(source_name: str) -> str:
    return (
        "Extract current public trend signals from this page for print-on-demand "
        "product research. Return JSON with a top-level `trends` array. Each item "
        "must include `keyword` as a short phrase, optional `engagement_score` as "
        "an integer, and optional `category`. Do not include personal data, account "
        f"data, login-only data, or raw page content. Source name: {source_name}."
    )


def _coerce_score(value: Any, fallback: int) -> int:
    if isinstance(value, bool):
        return fallback
    if isinstance(value, (int, float)):
        return max(0, int(value))
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits:
            return int(digits)
    return fallback


def normalize_scrapegraph_result(
    source_name: str,
    payload: Any,
) -> List[Dict[str, Any]]:
    if isinstance(payload, dict):
        raw_items = payload.get("trends") or payload.get("items") or payload.get("keywords")
        if raw_items is None and payload.get("keyword"):
            raw_items = [payload]
    elif isinstance(payload, list):
        raw_items = payload
    else:
        raw_items = None

    if not isinstance(raw_items, list):
        return []

    normalized: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_items):
        if isinstance(item, str):
            keyword = item
            score = max(10, 100 - index)
            category = "other"
        elif isinstance(item, dict):
            keyword = (
                item.get("keyword")
                or item.get("term")
                or item.get("trend")
                or item.get("title")
            )
            score = _coerce_score(item.get("engagement_score") or item.get("score"), max(10, 100 - index))
            category = str(item.get("category") or "other").strip().lower() or "other"
        else:
            continue

        keyword_text = " ".join(str(keyword or "").split()).strip()
        if not keyword_text:
            continue
        dedupe_key = keyword_text.lower()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        normalized.append(
            {
                "source": source_name,
                "keyword": keyword_text,
                "engagement_score": score,
                "category": category,
                "method": "scrapegraph",
            }
        )
    return normalized


def _run_scrapegraph(source_name: str, config: SourceConfig) -> Any:
    try:
        from scrapegraphai.graphs import SmartScraperGraph
    except Exception as exc:  # pragma: no cover - depends on optional package
        raise ScrapeGraphUnavailable("scrapegraphai package is unavailable") from exc

    graph = SmartScraperGraph(
        prompt=_prompt_for(source_name),
        source=config.url,
        config=_graph_config(),
    )
    return graph.run()


async def scrape_with_scrapegraph(
    source_name: str,
    config: SourceConfig,
) -> List[Dict[str, Any]]:
    validate_public_only_config()
    if not SCRAPEGRAPH_ENABLED:
        raise ScrapeGraphUnavailable("ScrapeGraphAI trend extraction is disabled")

    payload = await asyncio.to_thread(_run_scrapegraph, source_name, config)
    results = normalize_scrapegraph_result(source_name, payload)
    if not results:
        logger.info("ScrapeGraphAI returned no trends for %s", source_name)
    return results
