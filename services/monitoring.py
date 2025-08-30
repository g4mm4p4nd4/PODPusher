import os
import time
from typing import Awaitable, Callable, Optional
from fastapi import APIRouter, FastAPI, HTTPException, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from sqlalchemy import text
from .common.database import get_session
from .logging import LoggingMiddleware

REQUEST_COUNT = Counter(
    "request_count", "Total request count", ["service", "method", "path", "status"]
)
REQUEST_LATENCY = Histogram(
    "request_latency_seconds", "Request latency", ["service", "method", "path"]
)
REQUEST_ERRORS = Counter(
    "request_errors_total", "Request errors", ["service", "method", "path", "status"]
)


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            REQUEST_ERRORS.labels(
                self.service_name, request.method, request.url.path, str(status_code)
            ).inc()
            raise
        finally:
            duration = time.time() - start
            REQUEST_COUNT.labels(
                self.service_name, request.method, request.url.path, str(status_code)
            ).inc()
            REQUEST_LATENCY.labels(
                self.service_name, request.method, request.url.path
            ).observe(duration)


async def check_db() -> bool:
    try:
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def setup_monitoring(
    app: FastAPI,
    service_name: str,
    readiness_check: Optional[Callable[[], Awaitable[bool]]] = None,
) -> None:
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(MetricsMiddleware, service_name=service_name)

    router = APIRouter()

    @router.get("/metrics")
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @router.get("/health")
    async def health() -> dict:
        db_ok = await check_db()
        return {
            "status": "ok" if db_ok else "degraded",
            "database": db_ok,
            "version": os.getenv("APP_VERSION", "0.1.0"),
        }

    @router.get("/ready")
    async def ready() -> dict:
        db_ok = await check_db()
        ext_ok = True
        if readiness_check:
            ext_ok = await readiness_check()
        if db_ok and ext_ok:
            return {"status": "ready"}
        raise HTTPException(status_code=503, detail="not ready")

    app.include_router(router)
