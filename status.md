# Status and Outstanding Tasks

This file tracks the remaining work required to bring PODPusher to production readiness.

> **See Also:** [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md) for full development roadmap and [TASKS.md](./TASKS.md) for granular task breakdown.

## Current Sprint: MVP Completion

**Target:** Production-ready MVP
**Completion:** ~100% Phase 0 + Phase 1 + Phase 2 (Phase 3 remaining)

## Phase Status Summary

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 0: Critical MVP Blockers | **COMPLETE** | 100% |
| Phase 1: Core Experience Polish | **COMPLETE** | 100% |
| Phase 2: Enhanced Reliability | **COMPLETE** | 100% |
| Phase 3: Launch Preparation | Not Started | 0% |

## Pending PRs

- **Image Review & Tagging PR** - from the `feat/image-review-merge` branch via Codex. Review and merge once complete.

## Critical Blockers (P0) - RESOLVED

1. ~~**OAuth UI Integration**~~ - COMPLETE. OAuthConnect component, ProviderContext, settings page integration, token refresh, E2E tests all implemented.
2. ~~**Stripe Billing Integration**~~ - COMPLETE. Webhook handling (5 event types), customer portal, tier-specific quota enforcement, comprehensive test suite.

## Outstanding Tasks (P1) - RESOLVED

1. ~~**Localization & Internationalization (i18n)**~~ - COMPLETE. All 4 locales (EN, ES, FR, DE) with full key parity. ICU currency formatting utility. Extraction script. Expanded E2E tests for all locales.
2. ~~**Live Trend Signals Ingestion**~~ - COMPLETE. All 5 platforms (TikTok, Instagram, Twitter, Pinterest, Etsy) configured. Circuit breaker pattern. Prometheus scrape metrics. Auth-protected refresh endpoint. Scraper status endpoint.
3. ~~**Settings Page Completion**~~ - COMPLETE. Notification channel toggles (email/push), language selector, currency preference, timezone selector, TikTok handle, quota usage breakdown, upgrade CTA linked to Stripe portal.

## Remaining Work (P2 - Phase 3+)

1. ~~**Error Handling Standardization**~~ - COMPLETE. Unified APIError model, provider error mapping (Printify/Etsy/OpenAI), frontend ErrorBoundary, request ID tracking.
2. ~~**Rate Limiting**~~ - COMPLETE. Per-user/per-IP token bucket, external API rate limiting, frontend 429 handling with retry-after countdown.
3. ~~**Performance Optimization**~~ - COMPLETE. Caching layer (Redis/in-memory), DB indexing, Timescale continuous aggregates migration, slow query profiling, image lazy loading, frontend ErrorBoundary.
4. **Security Audit** - Input validation, auth review, secrets scan, vulnerability scan, STRIDE threat model.
5. **Documentation** - User docs, developer docs, provider guides, release notes.
6. **Load Testing** - k6 test suite, Grafana dashboards, SLO alerts.

## Completed

- Documentation Refresh - Internal docs now cover observability and database operations; architecture overview added in `docs/architecture.md`.
- Database Migrations - Alembic baseline created with scheduled notification migration, CLI helper, and CI upgrade check.
- Observability Rollout - Structured logging, `/healthz`, and `/metrics` endpoints registered across gateway, auth, notifications, trend scraper, and trend ingestion services.
- Notification & Scheduling System - Scheduled notifications API, recurring digests, and quota reset automation wired to APScheduler.
- A/B Testing Support - Flexible engine with experiment types, weighted traffic and scheduling.
- Real Integrations - Printify and Etsy clients implemented with stub fallbacks.
- Stub Removal - Placeholder logic eliminated and integrations call real APIs when keys are present.
- Listing Composer Enhancements - Drag-and-drop fields, improved tag suggestions, draft saving, multi-language input.
- Analytics Enhancements - Replaced mocked analytics with real metrics collected from the database and user interactions.
- Social Media Generator - Rule-based captions and images with localisation and dashboard UI.
- Bulk Product Creation - CSV/JSON bulk upload endpoint and UI implemented.
- Testing & QA - Expanded unit, integration, and Playwright end-to-end test coverage with CI integration.
- **OAuth UI Integration (Phase 0.1)** - OAuthConnect component with status badges, ProviderContext with expiry tracking, settings page integration, generate page gating, token refresh rotation, E2E tests.
- **Stripe Billing Integration (Phase 0.2)** - Full billing service (api, service, webhooks, plans), 5 webhook event handlers, portal endpoint, tier-specific quota enforcement, comprehensive test suite (468 lines).
- **i18n Expansion (Phase 1.1)** - 4 locales (EN, ES, FR, DE) with 170+ keys each. `scripts/i18n_extract.ts` extraction script. `client/services/currency.ts` ICU formatting utility. Updated `next-i18next.config.js`. Expanded E2E locale tests.
- **Live Trend Scrapers (Phase 1.2)** - All 5 platforms configured (TikTok, Instagram, Twitter, Pinterest, Etsy). Circuit breaker (`services/trend_ingestion/circuit_breaker.py`). Prometheus scrape metrics. Auth on refresh endpoint. Scraper status endpoint. Comprehensive test coverage.
- **Settings Page Polish (Phase 1.3)** - Notification toggles (email/push). Language/currency/timezone selectors. TikTok handle input. Quota usage breakdown by resource type. Upgrade CTA to Stripe portal. Backend preferences API extended with 5 new fields. Handle format validation (frontend regex + backend Pydantic).
- **Currency Formatting E2E Tests (Phase 1.1.6)** - 6 Playwright E2E tests exercising USD/EUR/GBP/CAD formatting across EN/ES/FR/DE locales. Currency selector persistence test.
- **Grafana Scraper Health Dashboard (Phase 1.2.7)** - `grafana/dashboards/scraper-health.json` with 8 panels: success/failure rates, failure gauge, duration quantiles, keyword extraction, cumulative stats, circuit breaker events, average duration by platform. Platform template variable.
- **Prometheus Alert Rules (Phase 1.2.7)** - `prometheus/alerts/scraper.yml` with 6 alert rules: high failure rate (>=5%), critical failure rate (>=25%), circuit breaker open, no scrape activity, slow duration (p95>20s), low keyword extraction.
- **Scraper Outage Runbook (Phase 1.2.7)** - `docs/runbooks/scraper-outage.md` covering circuit breaker states, diagnosis steps, manual refresh, circuit breaker reset, proxy rotation troubleshooting, selector updates, environment variables, escalation protocol.
- **RTL Support** - Deferred (internal tool only, no Arabic/Hebrew locale needed).
- **Error Handling Standardization (Phase 2.1)** - `services/common/errors.py` with APIError model, ErrorCode enum, request ID middleware. `services/common/provider_errors.py` with Printify/Etsy/OpenAI error mapping (20+ error codes). Integration service updated with try/catch and user-friendly messages. Frontend `ErrorBoundary.tsx` with "Try Again" action. `client/services/httpClient.ts` with standardized error classes. 29 tests covering all error scenarios.
- **Rate Limiting (Phase 2.2)** - `services/common/rate_limit.py` with per-user (plan-tier) and per-IP token bucket middleware. `services/common/api_limiter.py` with async token buckets for Printify (5 req/s), Etsy (10 req/s), OpenAI (3 req/s). Gateway integrated. Frontend `RateLimitBanner.tsx` with countdown UI. `httpClient.ts` with retry-after awareness.
- **Performance Optimization (Phase 2.3)** - `services/common/cache.py` with Redis/in-memory LRU cache (TTL support). Gateway /trends and /api/trends/live endpoints cached. Database model indexes added to 6 models (Trend, TrendSignal, Product, Notification, AnalyticsEvent fields). `grafana/dashboards/api-latency.json` with 6 panels. `prometheus/alerts/performance.yml` with 6 alert rules. 75 total tests passing.
- **Timescale Continuous Aggregates (TD-01)** - `alembic/versions/0003_timescale_trend_aggregates.py` migration with PostgreSQL/SQLite detection. Creates hypertable on `trendsignal`, hourly/daily continuous aggregates, refresh policies (30min/6h), 90-day retention policy. Composite indexes on both backends.
- **Slow Query Profiling (Phase 2.3.2)** - `services/common/database.py` rewritten with SQLAlchemy event listeners for `before_cursor_execute`/`after_cursor_execute`. Configurable threshold via `SLOW_QUERY_THRESHOLD_MS` env var (default 200ms). PostgreSQL connection pooling (pool_size=10, max_overflow=20, pool_pre_ping=True).
- **Image Lazy Loading (Phase 2.3.3)** - Added `loading="lazy"` and `decoding="async"` to `<img>` tags in `ImageCard.tsx`, `search.tsx`, and `SocialMediaGenerator.tsx`. `ImageCard` wrapped with `React.memo()` for render optimization.

## Instructions to Agents

Please refer to the appended section in `agents.md` for specific instructions on how each agent should tackle these tasks.
