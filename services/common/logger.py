import sys
import uuid
from contextvars import ContextVar
from loguru import logger
from fastapi import Request

_correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def init_logger() -> logger.__class__:
    """Configure loguru to emit structured JSON with correlation IDs."""
    logger.remove()
    logger.add(sys.stdout, serialize=True)

    def _patch(record):
        record["extra"]["correlation_id"] = _correlation_id_ctx.get()

    logger.configure(patcher=_patch)
    return logger


async def logging_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    token = _correlation_id_ctx.set(correlation_id)
    try:
        response = await call_next(request)
    finally:
        _correlation_id_ctx.reset(token)
    response.headers["X-Correlation-ID"] = correlation_id
    return response
