import time
import uuid
from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from .logging import request_id_ctx

REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "path", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds", "Request latency", ["method", "path"]
)
REQUEST_ERRORS = Counter(
    "http_request_errors_total", "Request errors", ["method", "path", "status"]
)


def setup_monitoring(app: FastAPI) -> None:
    """Attach monitoring middleware and endpoints to the app."""

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        request_id_ctx.set(str(uuid.uuid4()))
        start = time.time()
        try:
            response: Response = await call_next(request)
        except Exception as exc:  # pragma: no cover - simple error path
            duration = time.time() - start
            status = getattr(exc, "status_code", 500)
            REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)
            REQUEST_COUNT.labels(request.method, request.url.path, status).inc()
            REQUEST_ERRORS.labels(request.method, request.url.path, status).inc()
            raise
        duration = time.time() - start
        REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)
        REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
        response.headers["X-Request-ID"] = request_id_ctx.get() or ""
        return response

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/ready")
    async def ready():
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
