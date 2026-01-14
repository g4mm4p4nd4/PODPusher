"""Observability utilities (logging + metrics) for FastAPI apps."""
from __future__ import annotations

import time
from typing import Callable

from fastapi import FastAPI, Request
try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
except ModuleNotFoundError:  # pragma: no cover - fallback when optional dependency missing
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    class _CounterHandle:
        def __init__(self, parent, key):
            self._parent = parent
            self._key = key

        def inc(self, amount: float = 1.0) -> None:
            self._parent.values[self._key] = self._parent.values.get(self._key, 0.0) + amount

    class _HistogramHandle:
        def __init__(self, parent, key):
            self._parent = parent
            self._key = key

        def observe(self, value: float) -> None:
            bucket = self._parent.values.setdefault(self._key, {"count": 0, "sum": 0.0})
            bucket["count"] += 1
            bucket["sum"] += float(value)

    class _BaseMetric:
        def __init__(self, name: str, documentation: str, labelnames: tuple[str, ...]):
            self.name = name
            self.documentation = documentation
            self.labelnames = labelnames
            self.values: dict[tuple[str, ...], dict[str, float] | float] = {}

        def _label_key(self, label_values: tuple[str, ...]) -> tuple[str, ...]:
            if len(label_values) != len(self.labelnames):
                raise ValueError("Label value count does not match definition")
            return label_values

    class _FallbackCounter(_BaseMetric):
        registry: list["_FallbackCounter"] = []

        def __init__(self, name: str, documentation: str, labelnames: tuple[str, ...]):
            super().__init__(name, documentation, labelnames)
            self.__class__.registry.append(self)

        def labels(self, *label_values: str) -> _CounterHandle:
            key = self._label_key(tuple(label_values))
            self.values.setdefault(key, 0.0)
            return _CounterHandle(self, key)

    class _FallbackHistogram(_BaseMetric):
        registry: list["_FallbackHistogram"] = []

        def __init__(self, name: str, documentation: str, labelnames: tuple[str, ...]):
            super().__init__(name, documentation, labelnames)
            self.__class__.registry.append(self)

        def labels(self, *label_values: str) -> _HistogramHandle:
            key = self._label_key(tuple(label_values))
            self.values.setdefault(key, {"count": 0, "sum": 0.0})
            return _HistogramHandle(self, key)

    def Counter(name: str, documentation: str, labelnames: tuple[str, ...]):  # type: ignore[override]
        return _FallbackCounter(name, documentation, labelnames)

    def Histogram(name: str, documentation: str, labelnames: tuple[str, ...]):  # type: ignore[override]
        return _FallbackHistogram(name, documentation, labelnames)

    def generate_latest() -> bytes:
        lines: list[str] = []
        for metric in _FallbackCounter.registry:
            lines.append(f"# HELP {metric.name} {metric.documentation}")
            lines.append(f"# TYPE {metric.name} counter")
            for labels, value in metric.values.items():
                label_text = ",".join(f"{k}=\"{v}\"" for k, v in zip(metric.labelnames, labels))
                lines.append(f"{metric.name}{{{label_text}}} {value}")
        for metric in _FallbackHistogram.registry:
            lines.append(f"# HELP {metric.name} {metric.documentation}")
            lines.append(f"# TYPE {metric.name} summary")
            for labels, stats in metric.values.items():
                label_text = ",".join(f"{k}=\"{v}\"" for k, v in zip(metric.labelnames, labels))
                count = stats["count"]  # type: ignore[index]
                total = stats["sum"]  # type: ignore[index]
                lines.append(f"{metric.name}_count{{{label_text}}} {count}")
                lines.append(f"{metric.name}_sum{{{label_text}}} {total}")
        return "\n".join(lines).encode()
from starlette.responses import PlainTextResponse, Response

from .logging import configure_logging

REQUEST_COUNTER = Counter(
    "pod_request_total",
    "HTTP requests processed",
    labelnames=("service", "method", "path", "status"),
)
REQUEST_LATENCY = Histogram(
    "pod_request_latency_seconds",
    "HTTP request latency",
    labelnames=("service", "method", "path"),
)


def register_observability(app: FastAPI, *, service_name: str) -> None:
    """Attach logging, metrics, and health endpoints to app."""
    configure_logging()

    if getattr(app.state, "_observability_configured", False):
        return

    app.state._observability_configured = True

    @app.middleware("http")
    async def _metrics_middleware(request: Request, call_next: Callable):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration = time.perf_counter() - start
            path_template = _path_template(request)
            REQUEST_COUNTER.labels(service_name, request.method, path_template, "500").inc()
            REQUEST_LATENCY.labels(service_name, request.method, path_template).observe(duration)
            raise

        duration = time.perf_counter() - start
        path_template = _path_template(request)
        if not path_template.startswith("/metrics"):
            REQUEST_COUNTER.labels(
                service_name, request.method, path_template, str(response.status_code)
            ).inc()
            REQUEST_LATENCY.labels(service_name, request.method, path_template).observe(duration)
        return response

    @app.get("/healthz", include_in_schema=False)
    async def _healthz():
        return {"status": "ok"}

    @app.get("/metrics", include_in_schema=False)
    async def _metrics():
        payload = generate_latest()
        return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


def _path_template(request: Request) -> str:
    route = request.scope.get("route")
    if route and getattr(route, "path", None):
        return route.path  # type: ignore[return-value]
    return request.url.path


__all__ = [
    "register_observability",
    "REQUEST_COUNTER",
    "REQUEST_LATENCY",
]
