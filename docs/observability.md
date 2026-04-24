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
- The local Docker stack provisions Prometheus at `http://localhost:9090` and Grafana at `http://localhost:3001` with the default `admin` / `admin` login.
- Prometheus scrapes the gateway and trend ingestion services through `prometheus/prometheus.yml`, including scraper metrics for extraction method, fallback use, persisted signals, failures, and request latency.

## Local Trend Smoke
1. Start the no-key local stack:
   ```bash
   docker compose up --build
   ```
2. Trigger a public trend refresh:
   ```bash
   curl -X POST -H "X-User-Id: 1" http://localhost:8000/api/trends/refresh
   ```
3. Inspect the audit payload:
   ```bash
   curl http://localhost:8000/api/trends/live/status
   ```
4. Confirm `last_mode` is `live`, `source_methods` includes non-stub methods such as `scrapegraph`, `selector_fallback`, or `rss_fallback`, and `signals_persisted` is greater than zero.
5. Open Grafana and inspect the `Scraper Health` dashboard for `pod_scrape_method_total` and `pod_scrape_persisted_total`.

The trend scraper is public-only in this slice. Cookie files, exported browser sessions, usernames, passwords, and login URLs are rejected by configuration before scraping starts.

## Instrumentation Checklist
1. Import `register_observability` in any new FastAPI service and call it immediately after instantiating the app.
2. Add the helper to remaining micro-services that are not yet covered on `main`.
3. Ensure Prometheus scrapes the new endpoints and update Grafana dashboards plus alert rules accordingly.

## Next Steps
1. Propagate request IDs through upstream clients and include them in any manual log messages that cross service boundaries.
2. Forward structured logs to Loki and hook alerting into PagerDuty.
3. Capture background task duration metrics (Celery) and database connection pool metrics.
