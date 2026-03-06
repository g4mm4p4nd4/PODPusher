"""Tests for standardized error handling, rate limiting, and caching.

Owner: Unit-Tester (per DEVELOPMENT_PLAN.md Phase 2)
"""

import pytest
import time
from unittest.mock import MagicMock

import httpx

# ---------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------


class TestErrorSchema:
    """Test the standardized error schema."""

    def test_api_error_model(self):
        from services.common.errors import APIError

        err = APIError(
            code="INTERNAL_ERROR",
            message="Something broke",
            request_id="req-123",
        )
        assert err.code == "INTERNAL_ERROR"
        assert err.message == "Something broke"
        assert err.request_id == "req-123"
        assert err.details is None

    def test_api_error_with_details(self):
        from services.common.errors import APIError

        err = APIError(
            code="VALIDATION_ERROR",
            message="Invalid input",
            details={"field": "email", "reason": "required"},
            request_id="req-456",
        )
        assert err.details == {"field": "email", "reason": "required"}

    def test_error_code_enum_values(self):
        from services.common.errors import ErrorCode

        assert ErrorCode.INTERNAL_ERROR.value == "INTERNAL_ERROR"
        assert ErrorCode.RATE_LIMITED.value == "RATE_LIMITED"
        assert ErrorCode.PRINTIFY_ERROR.value == "PRINTIFY_ERROR"
        assert ErrorCode.ETSY_ERROR.value == "ETSY_ERROR"
        assert ErrorCode.OPENAI_CONTENT_POLICY.value == "OPENAI_CONTENT_POLICY"

    def test_app_error_exception(self):
        from services.common.errors import AppError, ErrorCode

        exc = AppError(
            code=ErrorCode.PRINTIFY_ERROR,
            message="Printify is down",
            status_code=502,
            details={"retryable": True},
        )
        assert exc.code == ErrorCode.PRINTIFY_ERROR
        assert exc.status_code == 502
        assert "Printify is down" in str(exc)

    def test_status_to_error_code_mapping(self):
        from services.common.errors import _status_to_error_code, ErrorCode

        assert _status_to_error_code(401) == ErrorCode.UNAUTHORIZED
        assert _status_to_error_code(403) == ErrorCode.FORBIDDEN
        assert _status_to_error_code(404) == ErrorCode.NOT_FOUND
        assert _status_to_error_code(429) == ErrorCode.RATE_LIMITED
        assert _status_to_error_code(999) == ErrorCode.INTERNAL_ERROR


# ---------------------------------------------------------------
# Provider error mapping tests
# ---------------------------------------------------------------


class TestProviderErrors:
    """Test provider-specific error mapping."""

    def test_printify_400_maps_to_validation(self):
        from services.common.provider_errors import handle_printify_error

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Invalid product data"}
        exc = httpx.HTTPStatusError("Bad Request", request=MagicMock(), response=mock_response)

        result = handle_printify_error(exc)
        assert result.code.value == "PRINTIFY_VALIDATION"
        assert "Invalid product data" in result.message

    def test_printify_401_maps_to_auth_error(self):
        from services.common.provider_errors import handle_printify_error

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {}
        exc = httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_response)

        result = handle_printify_error(exc)
        assert result.code.value == "PRINTIFY_AUTH_ERROR"

    def test_printify_429_maps_to_rate_limited(self):
        from services.common.provider_errors import handle_printify_error

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {}
        exc = httpx.HTTPStatusError("Rate Limited", request=MagicMock(), response=mock_response)

        result = handle_printify_error(exc)
        assert result.code.value == "PRINTIFY_RATE_LIMITED"

    def test_printify_timeout_handled(self):
        from services.common.provider_errors import handle_printify_error

        exc = httpx.TimeoutException("Connection timed out")
        result = handle_printify_error(exc)
        assert result.status_code == 504
        assert "timed out" in result.message

    def test_etsy_400_maps_to_validation(self):
        from services.common.provider_errors import handle_etsy_error

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {}
        exc = httpx.HTTPStatusError("Bad Request", request=MagicMock(), response=mock_response)

        result = handle_etsy_error(exc)
        assert result.code.value == "ETSY_VALIDATION"

    def test_etsy_listing_fee_error(self):
        from services.common.provider_errors import handle_etsy_error

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Listing fee payment required"}
        exc = httpx.HTTPStatusError("Bad Request", request=MagicMock(), response=mock_response)

        result = handle_etsy_error(exc)
        assert result.code.value == "ETSY_LISTING_FEE"

    def test_openai_content_policy(self):
        from services.common.provider_errors import handle_openai_error

        exc = Exception("Your request was rejected due to content_policy violation")
        result = handle_openai_error(exc)
        assert result.code.value == "OPENAI_CONTENT_POLICY"
        assert result.status_code == 400

    def test_openai_rate_limit(self):
        from services.common.provider_errors import handle_openai_error

        exc = Exception("Rate limit exceeded. Please retry after 429")
        result = handle_openai_error(exc)
        assert result.code.value == "OPENAI_RATE_LIMITED"

    def test_openai_token_limit(self):
        from services.common.provider_errors import handle_openai_error

        exc = Exception("This model's maximum context_length is 4096 tokens")
        result = handle_openai_error(exc)
        assert result.code.value == "OPENAI_TOKEN_LIMIT"


# ---------------------------------------------------------------
# Rate limiting tests
# ---------------------------------------------------------------


class TestRateLimiting:
    """Test the rate limiting middleware components."""

    def test_token_bucket_allows_within_limit(self):
        from services.common.rate_limit import TokenBucket

        bucket = TokenBucket(capacity=10)
        for _ in range(10):
            allowed, headers = bucket.allow()
            assert allowed
        assert int(headers["X-RateLimit-Limit"]) == 10

    def test_token_bucket_blocks_over_limit(self):
        from services.common.rate_limit import TokenBucket

        bucket = TokenBucket(capacity=5)
        for _ in range(5):
            bucket.allow()
        allowed, headers = bucket.allow()
        assert not allowed
        assert "Retry-After" in headers

    def test_token_bucket_refills_over_time(self):
        from services.common.rate_limit import TokenBucket

        bucket = TokenBucket(capacity=1)
        bucket.allow()  # consume the single token
        allowed, _ = bucket.allow()
        assert not allowed

        # Simulate time passing (refill)
        bucket.last_refill -= 61  # 61 seconds ago
        allowed, _ = bucket.allow()
        assert allowed

    def test_rate_limiter_per_key(self):
        from services.common.rate_limit import RateLimiter

        limiter = RateLimiter()
        allowed_a, _ = limiter.check("user:1", 5)
        allowed_b, _ = limiter.check("user:2", 5)
        assert allowed_a
        assert allowed_b

    def test_plan_rate_limits_configured(self):
        from services.common.rate_limit import PLAN_RATE_LIMITS

        assert PLAN_RATE_LIMITS["free"] < PLAN_RATE_LIMITS["enterprise"]
        assert "starter" in PLAN_RATE_LIMITS
        assert "professional" in PLAN_RATE_LIMITS


# ---------------------------------------------------------------
# External API rate limiter tests
# ---------------------------------------------------------------


class TestExternalAPILimiter:
    """Test async token bucket for provider rate limiting."""

    def test_provider_limits_configured(self):
        from services.common.api_limiter import PROVIDER_LIMITS

        assert "printify" in PROVIDER_LIMITS
        assert "etsy" in PROVIDER_LIMITS
        assert "openai" in PROVIDER_LIMITS
        # Printify should be 5 req/s
        rate, _ = PROVIDER_LIMITS["printify"]
        assert rate == 5.0
        # Etsy should be 10 req/s
        rate, _ = PROVIDER_LIMITS["etsy"]
        assert rate == 10.0

    def test_get_provider_limiter_creates_singleton(self):
        from services.common.api_limiter import get_provider_limiter

        limiter1 = get_provider_limiter("test_provider")
        limiter2 = get_provider_limiter("test_provider")
        assert limiter1 is limiter2


# ---------------------------------------------------------------
# Cache tests
# ---------------------------------------------------------------


class TestCache:
    """Test the caching layer."""

    def test_cache_set_and_get(self):
        from services.common.cache import cache_set, cache_get, cache_delete

        cache_set("test:key1", {"data": "hello"}, ttl=60)
        result = cache_get("test:key1")
        assert result == {"data": "hello"}
        cache_delete("test:key1")

    def test_cache_miss_returns_none(self):
        from services.common.cache import cache_get

        result = cache_get("test:nonexistent")
        assert result is None

    def test_cache_ttl_expiry(self):
        from services.common.cache import _mem_cache

        _mem_cache.set("test:expire", "value", ttl=0)
        # TTL of 0 means already expired
        time.sleep(0.01)
        result = _mem_cache.get("test:expire")
        assert result is None

    def test_cache_lru_eviction(self):
        from services.common.cache import InMemoryCache

        cache = InMemoryCache(max_size=3)
        cache.set("a", 1, ttl=60)
        cache.set("b", 2, ttl=60)
        cache.set("c", 3, ttl=60)
        cache.set("d", 4, ttl=60)  # should evict "a"
        assert cache.get("a") is None
        assert cache.get("d") == 4

    def test_cache_key_generation(self):
        from services.common.cache import cache_key

        k1 = cache_key("trends", "all")
        k2 = cache_key("trends", "all")
        k3 = cache_key("trends", "animals")
        assert k1 == k2
        assert k1 != k3
        assert k1.startswith("pod:")

    def test_cache_clear(self):
        from services.common.cache import _mem_cache

        _mem_cache.set("test:clear1", "a", ttl=60)
        _mem_cache.set("test:clear2", "b", ttl=60)
        _mem_cache.clear()
        assert _mem_cache.get("test:clear1") is None
        assert _mem_cache.get("test:clear2") is None

    def test_cache_delete(self):
        from services.common.cache import cache_set, cache_get, cache_delete

        cache_set("test:del", "val", ttl=60)
        assert cache_get("test:del") == "val"
        cache_delete("test:del")
        assert cache_get("test:del") is None

    def test_default_ttls_configured(self):
        from services.common.cache import CACHE_TTL_TRENDS, CACHE_TTL_IDEAS, CACHE_TTL_USER_QUOTA

        assert CACHE_TTL_TRENDS > 0
        assert CACHE_TTL_IDEAS > 0
        assert CACHE_TTL_USER_QUOTA > 0
