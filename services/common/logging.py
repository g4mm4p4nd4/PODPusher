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
