"""Shared logging configuration using structlog."""
from __future__ import annotations

import logging
import os
from typing import Any

try:
    import structlog  # type: ignore[import]
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    structlog = None  # type: ignore[assignment]

_CONFIGURED = False


def configure_logging(level: str | None = None) -> None:
    """Configure structlog + stdlib logging once for the process."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    numeric_level = logging.getLevelName(str(log_level).upper())
    if isinstance(numeric_level, str):
        numeric_level = logging.INFO
    logging.basicConfig(level=numeric_level, format="%(message)s")

    if structlog is not None:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_log_level,
                structlog.stdlib.filter_by_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    _CONFIGURED = True


def bind_request_context(*, request_id: str | None = None, user_id: int | str | None = None) -> None:
    """Bind per-request context fields to structlog, if available."""
    if structlog is None:
        return

    context: dict[str, Any] = {}
    if request_id is not None:
        context["request_id"] = request_id
    if user_id is not None:
        context["user_id"] = user_id

    if context:
        structlog.contextvars.bind_contextvars(**context)


def clear_request_context() -> None:
    """Clear any per-request structlog context."""
    if structlog is None:
        return

    structlog.contextvars.clear_contextvars()
