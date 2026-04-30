"""ScrapeGraphAI integration for public trend extraction.

The adapter is optional at import time so unit tests and non-Docker local
commands can run before the Docker image installs scrapegraphai.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
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
SCRAPEGRAPH_TIMEOUT_SECONDS = float(os.getenv("SCRAPEGRAPH_TIMEOUT_SECONDS", "45"))
SCRAPEGRAPH_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
SCRAPEGRAPH_OPENAI_BASE_URL = os.getenv("SCRAPEGRAPH_OPENAI_BASE_URL", "").rstrip("/")
SCRAPEGRAPH_API_KEY = (
    os.getenv("SCRAPEGRAPH_API_KEY")
    or os.getenv("OPENCODE_GO_API_KEY")
    or os.getenv("OPENCODE_API_KEY")
    or ""
)
OPENCODE_GO_BASE_URL = os.getenv(
    "OPENCODE_GO_BASE_URL", "https://opencode.ai/zen/go/v1"
).rstrip("/")
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


@dataclass(frozen=True)
class OpenAICompatibleModelRef:
    """Local fallback shape for config tests when langchain_openai is absent."""

    model_name: str
    openai_api_key: str
    openai_api_base: str
    streaming: bool = False


def validate_public_only_config() -> None:
    configured = [name for name in PUBLIC_ONLY_ENV_BLOCKLIST if os.getenv(name)]
    if configured:
        raise PublicOnlyConfigError(
            "Trend ingestion public-only mode rejects credential/session settings: "
            + ", ".join(configured)
        )


def _graph_config() -> Dict[str, Any]:
    model_name = SCRAPEGRAPH_MODEL
    llm_config: Dict[str, Any] = {
        "model": model_name,
        "model_tokens": SCRAPEGRAPH_MODEL_TOKENS,
        "format": "json",
    }
    if model_name.startswith("opencode-go/"):
        if not SCRAPEGRAPH_API_KEY:
            raise ScrapeGraphUnavailable(
                "OpenCode Go ScrapeGraph model requires OPENCODE_GO_API_KEY, "
                "OPENCODE_API_KEY, or SCRAPEGRAPH_API_KEY"
            )
        llm_config["model"] = f"oneapi/{model_name.split('/', 1)[1]}"
        llm_config["api_key"] = SCRAPEGRAPH_API_KEY
        llm_config["openai_api_base"] = OPENCODE_GO_BASE_URL
        try:
            from langchain_openai import ChatOpenAI
        except Exception as exc:  # pragma: no cover - dependency is installed in Docker
            logger.warning("langchain_openai package is unavailable: %s", exc)
            model_instance = OpenAICompatibleModelRef(
                model_name=model_name.split("/", 1)[1],
                openai_api_key=SCRAPEGRAPH_API_KEY,
                openai_api_base=OPENCODE_GO_BASE_URL,
                streaming=False,
            )
        else:
            model_instance = ChatOpenAI(
                model=model_name.split("/", 1)[1],
                openai_api_key=SCRAPEGRAPH_API_KEY,
                openai_api_base=OPENCODE_GO_BASE_URL,
                streaming=False,
            )
        llm_config = {
            "model_instance": model_instance,
            "model_tokens": SCRAPEGRAPH_MODEL_TOKENS,
        }
    elif model_name.startswith("oneapi/"):
        if SCRAPEGRAPH_API_KEY:
            llm_config["api_key"] = SCRAPEGRAPH_API_KEY
        if SCRAPEGRAPH_OPENAI_BASE_URL:
            llm_config["openai_api_base"] = SCRAPEGRAPH_OPENAI_BASE_URL
    elif model_name.startswith("ollama/") and SCRAPEGRAPH_OLLAMA_BASE_URL:
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
        "an integer, optional `category`, and optional `market_examples` with "
        "`title`, `source_url`, and `image_url` when public product examples or "
        "visual references are visible. Do not include personal data, account data, "
        "login-only data, raw page content, cookies, or browser session data. "
        f"Source name: {source_name}."
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
        raw_items = (
            payload.get("trends") or payload.get("items") or payload.get("keywords")
        )
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
            raw_examples = []
        elif isinstance(item, dict):
            keyword = (
                item.get("keyword")
                or item.get("term")
                or item.get("trend")
                or item.get("title")
            )
            score = _coerce_score(
                item.get("engagement_score") or item.get("score"), max(10, 100 - index)
            )
            category = str(item.get("category") or "other").strip().lower() or "other"
            raw_examples = item.get("market_examples") or item.get("examples") or []
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
                "market_examples": _coerce_market_examples(
                    source_name,
                    keyword_text,
                    score,
                    raw_examples if isinstance(raw_examples, list) else [],
                    item if isinstance(item, dict) else {},
                ),
            }
        )
    return normalized


def _coerce_market_examples(
    source_name: str,
    keyword: str,
    score: int,
    examples: List[Any],
    item: Dict[str, Any],
) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    candidates: List[Any] = [*examples]
    if item:
        candidates.append(
            {
                "title": (
                    item.get("example_title")
                    or item.get("product_title")
                    or item.get("title")
                    or keyword
                ),
                "source_url": item.get("source_url") or item.get("url") or item.get("link"),
                "image_url": (
                    item.get("image_url")
                    or item.get("thumbnail_url")
                    or item.get("image")
                ),
            }
        )
    for raw in candidates:
        if isinstance(raw, str):
            title = raw
            source_url = None
            image_url = None
        elif isinstance(raw, dict):
            title = raw.get("title") or raw.get("keyword") or raw.get("name") or keyword
            source_url = raw.get("source_url") or raw.get("url") or raw.get("link")
            image_url = raw.get("image_url") or raw.get("thumbnail_url") or raw.get("image")
        else:
            continue
        title_text = " ".join(str(title or "").split()).strip()
        if not title_text:
            continue
        normalized.append(
            {
                "title": title_text[:180],
                "keyword": keyword,
                "source": source_name,
                "source_url": source_url if isinstance(source_url, str) else None,
                "image_url": image_url if isinstance(image_url, str) else None,
                "engagement_score": score,
                "example_type": (
                    "source_product" if source_name in {"amazon", "etsy"} else "source_trend"
                ),
            }
        )
        if len(normalized) >= 5:
            break
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

    try:
        payload = await asyncio.wait_for(
            asyncio.to_thread(_run_scrapegraph, source_name, config),
            timeout=SCRAPEGRAPH_TIMEOUT_SECONDS,
        )
    except TimeoutError as exc:
        raise ScrapeGraphUnavailable(
            f"ScrapeGraphAI timed out after {SCRAPEGRAPH_TIMEOUT_SECONDS:g}s"
        ) from exc
    results = normalize_scrapegraph_result(source_name, payload)
    if not results:
        logger.info("ScrapeGraphAI returned no trends for %s", source_name)
    return results
