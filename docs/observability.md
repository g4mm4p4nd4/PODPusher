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
- Prometheus scrapes the gateway and trend ingestion services through `prometheus/prometheus.yml`, including scraper metrics for extraction method, fallback transitions, persisted signals, failures, circuit skips, and request latency.
- Alert rules live under `prometheus/alerts/`. Current local rules cover scraper failure rate, circuit breaker skips, no activity, slow scrapes, low keyword extraction, fallback spikes, RSS fallback dominance, gateway/API latency, 5xx rates, rate limiting, and composer publish-queue failures/latency. Queue alerts intentionally use local request metrics because Etsy and Printify publishing remain credential-gated and non-blocking.

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
5. Inspect `source_diagnostics` for each source. Healthy local evidence should include `status`, `method`, `collected`, `persisted`, `updated_at`, and, when fallback occurred, `fallback_from`, `fallback_to`, and `reason`.
6. Confirm `failed_count`, `fallback_count`, `skipped_count`, and `blocked_count` match the source rows. Circuit-open sources should appear in `sources_blocked` and `sources_skipped` so they are not confused with fresh extraction failures.
7. Inspect live trend payload metadata when validating pagination/sorting:
   ```bash
   curl "http://localhost:8000/api/trends/live?include_meta=true&sort_by=timestamp&sort_order=desc"
   ```
   Each returned signal carries provenance fields: `source`, `is_estimated`, `updated_at`, and `confidence`.
8. Open Grafana and inspect the `Scraper Health` dashboard for `pod_scrape_method_total`, `pod_scrape_fallback_total`, and `pod_scrape_persisted_total`.

The trend scraper is public-only in this slice. Cookie files, exported browser sessions, usernames, passwords, and login URLs are rejected by configuration before scraping starts.

## Local Workflow Smoke
1. Save a composer draft with local/demo copy:
   ```bash
   curl -X POST http://localhost:8000/api/listing-composer/drafts \
     -H "Content-Type: application/json" \
     -d '{"title":"Dog Mom Tee","description":"Local demo draft","tags":["dog mom"],"language":"en","field_order":["title","description","tags"]}'
   ```
2. Queue the draft with the returned ID:
   ```bash
   curl -X POST http://localhost:8000/api/listing-composer/drafts/1/publish-queue
   ```
3. Confirm the queue response reports `mode: demo`, `blocking: false` integration status for Etsy/Printify, and a retained `draft_id`.
4. Inspect local queue visibility:
   ```bash
   curl "http://localhost:8000/api/listing-composer/publish-queue?page=1&page_size=10"
   ```

## Instrumentation Checklist
1. Import `register_observability` in any new FastAPI service and call it immediately after instantiating the app.
2. Add the helper to remaining micro-services that are not yet covered on `main`.
3. Ensure Prometheus scrapes the new endpoints and update Grafana dashboards plus alert rules accordingly.

## Next Steps
1. Propagate request IDs through upstream clients and include them in any manual log messages that cross service boundaries.
2. Forward structured logs to Loki and hook alerting into PagerDuty.
3. Capture background task duration metrics (Celery) and database connection pool metrics.
