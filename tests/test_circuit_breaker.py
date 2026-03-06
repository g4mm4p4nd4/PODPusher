"""Tests for the trend ingestion circuit breaker.

Owner: Unit-Tester (per UT-01, UT-03)
Reference: DS-06 Monitoring & Alerting
"""
import time

from services.trend_ingestion.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    scraper_circuit_breaker,
)


def test_initial_state_is_closed():
    cb = CircuitBreaker()
    assert cb.state("tiktok") == CircuitState.CLOSED


def test_allow_request_when_closed():
    cb = CircuitBreaker()
    assert cb.allow_request("tiktok") is True


def test_opens_after_threshold_failures():
    cb = CircuitBreaker(failure_threshold=3)
    for _ in range(3):
        cb.record_failure("instagram")
    assert cb.state("instagram") == CircuitState.OPEN
    assert cb.allow_request("instagram") is False


def test_success_resets_failure_count():
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure("twitter")
    cb.record_failure("twitter")
    cb.record_success("twitter")
    assert cb.state("twitter") == CircuitState.CLOSED
    # Should not open even after one more failure
    cb.record_failure("twitter")
    assert cb.state("twitter") == CircuitState.CLOSED


def test_half_open_after_recovery_timeout():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
    cb.record_failure("etsy")
    assert cb.state("etsy") == CircuitState.OPEN
    time.sleep(0.02)
    assert cb.state("etsy") == CircuitState.HALF_OPEN


def test_half_open_allows_limited_calls():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01, half_open_max_calls=1)
    cb.record_failure("pinterest")
    time.sleep(0.02)
    assert cb.allow_request("pinterest") is True
    assert cb.allow_request("pinterest") is False


def test_half_open_success_closes_circuit():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
    cb.record_failure("tiktok")
    time.sleep(0.02)
    cb.record_success("tiktok")
    assert cb.state("tiktok") == CircuitState.CLOSED


def test_half_open_failure_reopens_circuit():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
    cb.record_failure("tiktok")
    time.sleep(0.02)
    assert cb.state("tiktok") == CircuitState.HALF_OPEN
    cb.record_failure("tiktok")
    assert cb.state("tiktok") == CircuitState.OPEN


def test_reset_clears_state():
    cb = CircuitBreaker(failure_threshold=1)
    cb.record_failure("twitter")
    assert cb.state("twitter") == CircuitState.OPEN
    cb.reset("twitter")
    assert cb.state("twitter") == CircuitState.CLOSED


def test_independent_platform_states():
    cb = CircuitBreaker(failure_threshold=2)
    cb.record_failure("tiktok")
    cb.record_failure("tiktok")
    assert cb.state("tiktok") == CircuitState.OPEN
    assert cb.state("instagram") == CircuitState.CLOSED


def test_singleton_instance_exists():
    assert scraper_circuit_breaker is not None
    assert isinstance(scraper_circuit_breaker, CircuitBreaker)
