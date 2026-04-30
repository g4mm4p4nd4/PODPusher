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

### April 30, 2026 Source Evidence

The latest local Docker smoke used the full Compose stack after fixing two local
Postgres migration issues: Timescale rollups now skip cleanly when the
`timescaledb` extension is unavailable, and Alembic revision IDs stay within
Postgres' default `alembic_version.version_num` length. Gateway, trend
ingestion, Prometheus, Grafana, frontend, Redis, Postgres, Ollama, and worker
containers reached healthy/running state.

Smoke command evidence:

- `POST /api/trends/refresh` completed in live mode with `signals_collected: 4`, `signals_persisted: 3`, `fallback_count: 6`, `skipped_count: 2`, and `blocked_count: 2`.
- `GET /api/trends/live/status` reported Amazon and TikTok success through `selector_fallback`; Etsy and X/Twitter were blocked/skipped; Pinterest, Instagram, and Google Trends RSS failed with zero persisted rows.
- `GET /api/trends/live?include_meta=true&sort_by=timestamp&sort_order=desc` returned provenance on every persisted row.
- `GET /metrics` exposed `pod_scrape_method_total`, `pod_scrape_fallback_total`, and `pod_scrape_persisted_total`; Prometheus returned `pod_scrape_persisted_total{source="amazon"} 2` and `{source="tiktok"} 1`.
- Browser QA loaded `http://127.0.0.1:3000/trends` through Chromium at desktop and mobile viewports with no page errors, no console errors, and no HTTP errors.

Observed source behavior:

| Source | Evidence | Runtime handling |
| --- | --- | --- |
| TikTok Creative Center | HTTP 200 public shell, but mostly navigation labels such as Trend Discovery, Top Ads, and Creative Insights in static text. | Keep as a live candidate, but noise filtering prevents shell labels from persisting. |
| Instagram explore tags | HTTP 200 shell with robot-gated content indicators. | Classified as blocked/login gated when Playwright sees bot or login markers. |
| X/Twitter explore | Redirected to `x.com/i/flow/login` and reported JavaScript/login gating. | Classified as blocked and counted in `sources_blocked`/`sources_skipped`. |
| Pinterest Today | Public page may either expose captcha markers or return no selector-safe POD rows. | Classified as blocked when captcha markers appear; otherwise records a normal selector failure with zero persisted rows. |
| Etsy trends and hubs | HTTP 403 captcha/JS gate. | Classified as blocked, not as a fresh selector failure. |
| Amazon movers and shakers | HTTP 200 public product pages; useful titles are available through `img alt` text. | Primary Amazon source is now Arts/Crafts, then Handmade, Home/Garden, and Fashion candidates. Selectors read `img[alt]`, and normalization condenses long product titles while rejecting brand/UI/bodywear noise and gift-only phrases. |
| Google Trends RSS | Current RSS sample was news/noise heavy and produced zero POD-oriented candidates after filtering. | RSS fallback only persists terms with concrete POD product nouns such as shirt, mug, poster, decor, hat, tote, bag, jewelry, or sticker. |

Blocked sources should degrade as `status: skipped`, `method: blocked`, and appear in `sources_blocked` with a sanitized `reason`. ScrapeGraphAI is capped by `SCRAPEGRAPH_TIMEOUT_SECONDS` before selector fallback to prevent slow public pages from holding the whole refresh open. No raw page bodies, cookies, browser sessions, usernames, passwords, or login flows should be stored or supplied.

## Local Workflow Smoke
1. Save a composer draft:
   ```bash
   curl -X POST http://localhost:8000/api/listing-composer/drafts \
     -H "Content-Type: application/json" \
     -d '{"title":"Dog Mom Tee","description":"Internal draft","tags":["dog mom"],"language":"en","field_order":["title","description","tags"]}'
   ```
2. Queue the draft with the returned ID:
   ```bash
   curl -X POST http://localhost:8000/api/listing-composer/drafts/1/publish-queue
   ```
3. Confirm the queue response reports `mode: implementation_required`, `status: needs_implementation`, `blocking: true` integration status for Etsy/Printify, and a retained `draft_id`. A queue record should never imply that a live Etsy or Printify publish occurred until those integrations are configured and implemented.
4. Inspect local queue visibility:
   ```bash
   curl "http://localhost:8000/api/listing-composer/publish-queue?page=1&page_size=10"
   ```

## Capability Status Smoke
Credential-backed surfaces should fail closed instead of returning local/demo success. Inspect the system contract before QA:

```bash
curl http://localhost:8000/api/system/capabilities
```

Expected no-key local evidence:

- `trend_refresh.status` is `live_public_only` when `TREND_INGESTION_STUB=0`.
- OpenAI, Etsy, Printify, and Stripe entries report `status: needs_implementation`, `configured: false`, and concrete `required` configuration when credentials are missing.
- Billing portal calls return HTTP `424` with `implementation_status: needs_implementation` rather than a fake portal URL.

## Instrumentation Checklist
1. Import `register_observability` in any new FastAPI service and call it immediately after instantiating the app.
2. Add the helper to remaining micro-services that are not yet covered on `main`.
3. Ensure Prometheus scrapes the new endpoints and update Grafana dashboards plus alert rules accordingly.

## Next Steps
1. Propagate request IDs through upstream clients and include them in any manual log messages that cross service boundaries.
2. Forward structured logs to Loki and hook alerting into PagerDuty.
3. Capture background task duration metrics (Celery) and database connection pool metrics.
