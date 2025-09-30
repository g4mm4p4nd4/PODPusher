# Status and Outstanding Tasks

This file tracks the remaining work required to bring PODPusher to production readiness.

## Pending PRs

- **Image Review & Tagging PR** - from the `feat/image-review-merge` branch via Codex. Review and merge once complete.

## Outstanding Tasks

1. **Localization & Internationalization (i18n)** - Extend translation support beyond current pages and adapt currency formats for different locales (translation key check script added, rollout pending).
2. **Live Trend Signals Ingestion** - Build Playwright scrapers and storage per Data-Seeder responsibilities in `agents.md`.
3. **OAuth UI & Flows** - Wire frontend connect/disconnect UX to the new auth endpoints and expand e2e coverage.

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
