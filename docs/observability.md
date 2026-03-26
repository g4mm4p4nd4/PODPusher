# Observability Playbook

## Logging
- Shared configuration lives in `services/common/logging.py` and is exposed through `configure_logging()`.
- `configure_logging()` initialises structlog with JSON output and is invoked automatically by `register_observability()` so new services rarely need to call it manually.
- `register_observability()` binds `request_id` and `user_id` into structlog contextvars for the life of each request, then clears them before the request finishes.

## Metrics
- `services/common/observability.py` exposes `register_observability(app, service_name=...)` to instrument FastAPI apps.
- The helper adds:
  - `/healthz` readiness endpoint returning `{"status": "ok"}`.
  - `/ready` endpoint that performs a lightweight database ping and returns `503` when the database is unavailable.
  - `/metrics` endpoint emitting Prometheus data for `pod_request_total` and `pod_request_latency_seconds`.
  - Middleware capturing HTTP method, templated path, status code, and latency for every request.
- Metrics are currently enabled for the gateway, analytics, auth, notifications, trend scraper, trend ingestion, ideation, integration, listing composer, search, social generator, user, and product services.

## Instrumentation Checklist
1. Import `register_observability` in any new FastAPI service and call it immediately after instantiating the app.
2. Add the helper to remaining micro-services that are not yet covered on `main`.
3. Ensure Prometheus scrapes the new endpoints and update Grafana dashboards plus alert rules accordingly.

## Next Steps
1. Propagate request IDs through upstream clients and include them in any manual log messages that cross service boundaries.
2. Forward structured logs to Loki and hook alerting into PagerDuty.
3. Capture background task duration metrics (Celery) and database connection pool metrics.
