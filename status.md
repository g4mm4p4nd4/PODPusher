# Status and Outstanding Tasks

This file tracks the remaining work required to bring PODPusher to production readiness.

> **See Also:** [DEVELOPMENT_PLAN.md](./DEVELOPMENT_PLAN.md) for full development roadmap and [TASKS.md](./TASKS.md) for granular task breakdown.

## Current Sprint: MVP Completion

**Target:** Production-ready MVP in 6-8 weeks
**Completion:** ~75-80%

## Pending PRs

- **Image Review & Tagging PR** - from the `feat/image-review-merge` branch via Codex. Review and merge once complete.

## Critical Blockers (P0)

1. **OAuth UI Integration** - Frontend connect/disconnect widgets needed in Settings page. Backend complete, frontend wiring required.
2. **Stripe Billing Integration** - Webhook handling, customer portal, quota enforcement by plan tier.

## Outstanding Tasks (P1)

1. **Localization & Internationalization (i18n)** - Extend translation support beyond current pages (~40% coverage). Add FR/DE locales. Implement ICU currency formatting.
2. **Live Trend Signals Ingestion** - Complete Playwright scrapers for TikTok, Instagram, Twitter, Pinterest, Etsy per Data-Seeder responsibilities.
3. **Settings Page Completion** - User preferences, notification channels, quota display with upgrade CTA.

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

## Instructions to Agents

Please refer to the appended section in `agents.md` for specific instructions on how each agent should tackle these tasks.
