import logging
import json
import sys
from datetime import datetime
import contextvars
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from uuid import uuid4

request_id_ctx = contextvars.ContextVar("request_id", default=None)
user_id_ctx = contextvars.ContextVar("user_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        request_id = getattr(record, "request_id", request_id_ctx.get())
        user_id = getattr(record, "user_id", user_id_ctx.get())
        if request_id:
            log_record["request_id"] = request_id
        if user_id:
            log_record["user_id"] = user_id
        return json.dumps(log_record)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        logger.propagate = True
    return logger


def set_context(
    request_id: Optional[str] = None, user_id: Optional[str] = None
) -> None:
    if request_id is not None:
        request_id_ctx.set(request_id)
    if user_id is not None:
        user_id_ctx.set(user_id)


def clear_context() -> None:
    request_id_ctx.set(None)
    user_id_ctx.set(None)


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, logger: Optional[logging.Logger] = None):
        super().__init__(app)
        self.logger = logger or get_logger(__name__)

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        user_id = request.headers.get("X-User-Id")
        set_context(request_id, user_id)
        self.logger.info(
            f"{request.method} {request.url.path}",
            extra={"request_id": request_id, "user_id": user_id},
        )
        try:
            response = await call_next(request)
            self.logger.info(
                f"{request.method} {request.url.path} - {response.status_code}",
                extra={"request_id": request_id, "user_id": user_id},
            )
            return response
        finally:
            clear_context()
