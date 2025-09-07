import os
import time
import uuid
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest, start_http_server

from .logging import logger
from .database import check_db_connection

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        response = Response(status_code=500)
        try:
            response = await call_next(request)
        finally:
            latency = time.perf_counter() - start_time
            REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
            REQUEST_LATENCY.labels(request.method, request.url.path).observe(latency)
            logger.bind(correlation_id=correlation_id).info(
                "request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                latency=latency,
            )
            response.headers["X-Correlation-ID"] = correlation_id
        return response


def setup_observability(app: FastAPI) -> None:
    app.add_middleware(ObservabilityMiddleware)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/ready")
    async def ready() -> Response:
        if await check_db_connection():
            return Response(status_code=200, content="ready")
        return Response(status_code=503, content="unavailable")

    @app.get("/metrics")
    async def metrics() -> Response:
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)

    port = os.getenv("METRICS_PORT")
    if port:
        start_http_server(int(port))
