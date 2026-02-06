# Status and Outstanding Tasks

This file tracks the remaining work required to bring PODPusher to production readiness.

> **See Also:** [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md) for full development roadmap and [TASKS.md](./TASKS.md) for granular task breakdown.

## Current Sprint: MVP Completion

**Target:** Production-ready MVP
**Completion:** ~90% (Phase 0 + Phase 1 complete)

## Phase Status Summary

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 0: Critical MVP Blockers | **COMPLETE** | 100% |
| Phase 1: Core Experience Polish | **COMPLETE** | 95% |
| Phase 2: Enhanced Reliability | Not Started | 0% |
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

## Remaining Work (P2 - Phase 2+)

1. **Error Handling Standardization** - Unified API error model, Printify/Etsy/OpenAI error mapping, frontend ErrorBoundary.
2. **Rate Limiting** - Per-user/per-IP limits, external API rate limits with aiolimiter, frontend 429 handling.
3. **Performance Optimization** - Redis caching, DB indexing, frontend React.memo/virtualization/code-splitting.
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
- **Settings Page Polish (Phase 1.3)** - Notification toggles (email/push). Language/currency/timezone selectors. TikTok handle input. Quota usage breakdown by resource type. Upgrade CTA to Stripe portal. Backend preferences API extended with 5 new fields.

## Instructions to Agents

Please refer to the appended section in `agents.md` for specific instructions on how each agent should tackle these tasks.
