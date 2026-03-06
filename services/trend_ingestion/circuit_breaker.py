"""Circuit breaker pattern for trend ingestion scrapers.

Implements a state machine (CLOSED -> OPEN -> HALF_OPEN) to prevent
cascading failures when scraping platforms go down.

Owner: Data-Seeder (per DS-06 Monitoring & Alerting)
Reference: agents_data_seeder.md §6.1 - Scraper Failure handling
"""
from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Dict

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Per-platform circuit breaker with configurable thresholds."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 300.0,
        half_open_max_calls: int = 1,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self._states: Dict[str, CircuitState] = {}
        self._failure_counts: Dict[str, int] = {}
        self._last_failure_time: Dict[str, float] = {}
        self._half_open_calls: Dict[str, int] = {}

    def state(self, platform: str) -> CircuitState:
        """Return current circuit state for a platform."""
        current = self._states.get(platform, CircuitState.CLOSED)
        if current == CircuitState.OPEN:
            last_failure = self._last_failure_time.get(platform, 0)
            if time.monotonic() - last_failure >= self.recovery_timeout:
                self._states[platform] = CircuitState.HALF_OPEN
                self._half_open_calls[platform] = 0
                logger.info("Circuit breaker HALF_OPEN for %s", platform)
                return CircuitState.HALF_OPEN
        return current

    def allow_request(self, platform: str) -> bool:
        """Check whether a scrape request is allowed for this platform."""
        current = self.state(platform)
        if current == CircuitState.CLOSED:
            return True
        if current == CircuitState.HALF_OPEN:
            calls = self._half_open_calls.get(platform, 0)
            if calls < self.half_open_max_calls:
                self._half_open_calls[platform] = calls + 1
                return True
            return False
        return False  # OPEN

    def record_success(self, platform: str) -> None:
        """Record a successful scrape — reset failure counter."""
        previous = self._states.get(platform, CircuitState.CLOSED)
        self._states[platform] = CircuitState.CLOSED
        self._failure_counts[platform] = 0
        self._half_open_calls.pop(platform, None)
        if previous != CircuitState.CLOSED:
            logger.info("Circuit breaker CLOSED for %s (recovered)", platform)

    def record_failure(self, platform: str) -> None:
        """Record a scrape failure — may trip the breaker to OPEN."""
        count = self._failure_counts.get(platform, 0) + 1
        self._failure_counts[platform] = count
        self._last_failure_time[platform] = time.monotonic()

        current = self.state(platform)
        if current == CircuitState.HALF_OPEN:
            self._states[platform] = CircuitState.OPEN
            logger.warning(
                "Circuit breaker OPEN for %s (half-open probe failed)", platform
            )
        elif count >= self.failure_threshold:
            self._states[platform] = CircuitState.OPEN
            logger.warning(
                "Circuit breaker OPEN for %s (failures=%d >= threshold=%d)",
                platform,
                count,
                self.failure_threshold,
            )

    def reset(self, platform: str) -> None:
        """Manually reset circuit state for a platform."""
        self._states.pop(platform, None)
        self._failure_counts.pop(platform, None)
        self._last_failure_time.pop(platform, None)
        self._half_open_calls.pop(platform, None)


# Singleton instance shared across the scraper service.
scraper_circuit_breaker = CircuitBreaker()
