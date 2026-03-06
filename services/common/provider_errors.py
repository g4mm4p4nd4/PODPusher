"""Provider-specific error mapping for Printify, Etsy, and OpenAI.

Translates third-party API errors into standardized AppError instances
with user-friendly messages.

Owner: Integrations-Engineer (per DEVELOPMENT_PLAN.md Task 2.1.2-2.1.4)
Reference: IN-05 (Error Handling & Logging), TD-02
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .errors import AppError, ErrorCode

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Printify error mapping
# ---------------------------------------------------------------------------

PRINTIFY_ERROR_MAP: dict[int, tuple[ErrorCode, str]] = {
    400: (ErrorCode.PRINTIFY_VALIDATION, "Invalid product data sent to Printify"),
    401: (ErrorCode.PRINTIFY_AUTH_ERROR, "Printify authentication failed — please reconnect your account"),
    403: (ErrorCode.PRINTIFY_AUTH_ERROR, "Printify access denied — check your API permissions"),
    404: (ErrorCode.PRINTIFY_NOT_FOUND, "Printify resource not found — the product or shop may have been removed"),
    429: (ErrorCode.PRINTIFY_RATE_LIMITED, "Printify rate limit reached — please wait a moment and try again"),
    500: (ErrorCode.PRINTIFY_ERROR, "Printify is experiencing issues — please try again later"),
    502: (ErrorCode.PRINTIFY_ERROR, "Printify is temporarily unreachable"),
    503: (ErrorCode.PRINTIFY_ERROR, "Printify is undergoing maintenance — please try again shortly"),
}


def handle_printify_error(exc: Exception, context: dict[str, Any] | None = None) -> AppError:
    """Map a Printify API error to a standardized AppError."""
    status_code = 502
    code = ErrorCode.PRINTIFY_ERROR
    message = "An error occurred while communicating with Printify"

    if isinstance(exc, httpx.HTTPStatusError):
        resp_status = exc.response.status_code
        mapped = PRINTIFY_ERROR_MAP.get(resp_status)
        if mapped:
            code, message = mapped
        status_code = 502 if resp_status >= 500 else resp_status
        # Try to extract Printify error details
        try:
            body = exc.response.json()
            detail = body.get("message") or body.get("error") or body.get("errors")
            if detail:
                context = {**(context or {}), "provider_detail": detail}
        except Exception:
            pass
    elif isinstance(exc, httpx.TimeoutException):
        code = ErrorCode.PRINTIFY_ERROR
        message = "Printify request timed out — please try again"
        status_code = 504
    elif isinstance(exc, httpx.ConnectError):
        code = ErrorCode.PRINTIFY_ERROR
        message = "Unable to reach Printify — check your network connection"
        status_code = 502

    logger.error("Printify error: %s", exc, extra={"provider": "printify", **(context or {})})
    return AppError(code=code, message=message, status_code=status_code, details=context)


# ---------------------------------------------------------------------------
# Etsy error mapping
# ---------------------------------------------------------------------------

ETSY_ERROR_MAP: dict[int, tuple[ErrorCode, str]] = {
    400: (ErrorCode.ETSY_VALIDATION, "Invalid listing data sent to Etsy"),
    401: (ErrorCode.ETSY_AUTH_ERROR, "Etsy authentication failed — please reconnect your account"),
    403: (ErrorCode.ETSY_AUTH_ERROR, "Etsy access denied — check your API permissions"),
    404: (ErrorCode.ETSY_NOT_FOUND, "Etsy resource not found — the shop or listing may have been removed"),
    409: (ErrorCode.ETSY_VALIDATION, "Etsy conflict — a listing with this data may already exist"),
    429: (ErrorCode.ETSY_RATE_LIMITED, "Etsy rate limit reached — please wait a moment and try again"),
    500: (ErrorCode.ETSY_ERROR, "Etsy is experiencing issues — please try again later"),
    503: (ErrorCode.ETSY_ERROR, "Etsy is undergoing maintenance — please try again shortly"),
}


def handle_etsy_error(exc: Exception, context: dict[str, Any] | None = None) -> AppError:
    """Map an Etsy API error to a standardized AppError."""
    status_code = 502
    code = ErrorCode.ETSY_ERROR
    message = "An error occurred while communicating with Etsy"

    if isinstance(exc, httpx.HTTPStatusError):
        resp_status = exc.response.status_code
        mapped = ETSY_ERROR_MAP.get(resp_status)
        if mapped:
            code, message = mapped
        # Check for listing fee errors
        try:
            body = exc.response.json()
            detail = body.get("error") or body.get("non_field_errors")
            if detail and "listing fee" in str(detail).lower():
                code = ErrorCode.ETSY_LISTING_FEE
                message = "Etsy listing fee payment required — check your Etsy billing settings"
            if detail:
                context = {**(context or {}), "provider_detail": detail}
        except Exception:
            pass
        status_code = 502 if resp_status >= 500 else resp_status
    elif isinstance(exc, httpx.TimeoutException):
        code = ErrorCode.ETSY_ERROR
        message = "Etsy request timed out — please try again"
        status_code = 504
    elif isinstance(exc, httpx.ConnectError):
        code = ErrorCode.ETSY_ERROR
        message = "Unable to reach Etsy — check your network connection"
        status_code = 502

    logger.error("Etsy error: %s", exc, extra={"provider": "etsy", **(context or {})})
    return AppError(code=code, message=message, status_code=status_code, details=context)


# ---------------------------------------------------------------------------
# OpenAI error mapping
# ---------------------------------------------------------------------------

def handle_openai_error(exc: Exception, context: dict[str, Any] | None = None) -> AppError:
    """Map an OpenAI API error to a standardized AppError."""
    code = ErrorCode.OPENAI_ERROR
    message = "An error occurred with AI generation"
    status_code = 502

    exc_str = str(exc).lower()

    if "content_policy" in exc_str or "content policy" in exc_str or "safety" in exc_str:
        code = ErrorCode.OPENAI_CONTENT_POLICY
        message = "Your request was flagged by content filters — please adjust your prompt and try again"
        status_code = 400
    elif "rate_limit" in exc_str or "rate limit" in exc_str or "429" in exc_str:
        code = ErrorCode.OPENAI_RATE_LIMITED
        message = "AI service rate limit reached — please wait a moment and try again"
        status_code = 429
    elif "context_length" in exc_str or "token" in exc_str and "maximum" in exc_str:
        code = ErrorCode.OPENAI_TOKEN_LIMIT
        message = "Input too long for AI processing — please shorten your request"
        status_code = 400
    elif "timeout" in exc_str:
        message = "AI generation timed out — please try again"
        status_code = 504

    logger.error("OpenAI error: %s", exc, extra={"provider": "openai", **(context or {})})
    return AppError(code=code, message=message, status_code=status_code, details=context)
