"""Standardized API error handling.

Provides a unified error response schema, error codes, request ID tracking,
and exception handlers for consistent error formatting across all services.

Owner: Backend-Coder (per DEVELOPMENT_PLAN.md Task 2.1.1)
Reference: BC-04 (Input Validation & Error Handling)
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorCode(str, Enum):
    """Standardized error codes for all API responses."""

    # Generic errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    RATE_LIMITED = "RATE_LIMITED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # Provider errors
    PRINTIFY_ERROR = "PRINTIFY_ERROR"
    PRINTIFY_RATE_LIMITED = "PRINTIFY_RATE_LIMITED"
    PRINTIFY_AUTH_ERROR = "PRINTIFY_AUTH_ERROR"
    PRINTIFY_NOT_FOUND = "PRINTIFY_NOT_FOUND"
    PRINTIFY_VALIDATION = "PRINTIFY_VALIDATION"

    ETSY_ERROR = "ETSY_ERROR"
    ETSY_RATE_LIMITED = "ETSY_RATE_LIMITED"
    ETSY_AUTH_ERROR = "ETSY_AUTH_ERROR"
    ETSY_NOT_FOUND = "ETSY_NOT_FOUND"
    ETSY_LISTING_FEE = "ETSY_LISTING_FEE"
    ETSY_VALIDATION = "ETSY_VALIDATION"

    OPENAI_ERROR = "OPENAI_ERROR"
    OPENAI_CONTENT_POLICY = "OPENAI_CONTENT_POLICY"
    OPENAI_RATE_LIMITED = "OPENAI_RATE_LIMITED"
    OPENAI_TOKEN_LIMIT = "OPENAI_TOKEN_LIMIT"

    # Scraper errors
    SCRAPER_CIRCUIT_OPEN = "SCRAPER_CIRCUIT_OPEN"
    SCRAPER_TIMEOUT = "SCRAPER_TIMEOUT"


class APIError(BaseModel):
    """Standardized API error response body."""

    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str


class AppError(Exception):
    """Application-level error that maps to a standardized API response."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def get_request_id(request: Request) -> str:
    """Extract or generate a request ID."""
    return request.headers.get("X-Request-Id") or str(uuid.uuid4())


def register_error_handlers(app: FastAPI) -> None:
    """Register standardized error handlers on a FastAPI app."""

    @app.middleware("http")
    async def _inject_request_id(request: Request, call_next):
        request.state.request_id = get_request_id(request)
        response = await call_next(request)
        response.headers["X-Request-Id"] = request.state.request_id
        return response

    @app.exception_handler(AppError)
    async def _app_error_handler(request: Request, exc: AppError):
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        return JSONResponse(
            status_code=exc.status_code,
            content=APIError(
                code=exc.code.value,
                message=exc.message,
                details=exc.details,
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def _http_error_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        code = _status_to_error_code(exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content=APIError(
                code=code.value,
                message=str(exc.detail),
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        return JSONResponse(
            status_code=422,
            content=APIError(
                code=ErrorCode.VALIDATION_ERROR.value,
                message="Request validation failed",
                details={"errors": exc.errors()},
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        return JSONResponse(
            status_code=500,
            content=APIError(
                code=ErrorCode.INTERNAL_ERROR.value,
                message="An unexpected error occurred",
                request_id=request_id,
            ).model_dump(),
        )


def _status_to_error_code(status_code: int) -> ErrorCode:
    """Map HTTP status codes to error codes."""
    mapping = {
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMITED,
        402: ErrorCode.QUOTA_EXCEEDED,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }
    return mapping.get(status_code, ErrorCode.INTERNAL_ERROR)
