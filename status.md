# Status and Outstanding Tasks

This file tracks the remaining work required to bring PODPusher to internal rollout readiness.

## Pending PRs

- **Image Review & Tagging PR** - from the `feat/image-review-merge` branch via Codex. Review and merge once complete.

## Current Focus

1. **Bootstraps & CI Hardening** - Replace the empty Alembic baseline, align runtime env/docs with the Etsy OAuth contract, and add frontend build plus type-check checks to CI.
2. **Real Trend Pipeline Validation** - Validate one non-stub trend -> idea -> image -> listing flow in staging when credentials are available.
3. **Docs & Multi-User Cleanup** - Remove merge artifacts, finish the remaining i18n rollout, and reduce lingering internal-user assumptions.

## Recently Completed

- **P0 Gateway/Client Recovery (March 6, 2026)** - Added the missing shared frontend API-base module, centralized authenticated headers, wired OAuth, generate, quota, and notifications through that shared transport, mounted user and analytics routes in the gateway, and fixed the gateway lifespan declaration.
- **Mainline Consolidation Sweep (March 6, 2026)** - Folded detached worktree output back into the main workspace for live trend dashboard/status flows, live analytics keyword aggregation, and OAuth API error mapping.
- **Trend Ingestion Hardening** - Added refresh telemetry, live status endpoints, live trend filtering/recency bounds, RSS fallback handling, and focused backend/frontend coverage.
- **Analytics Truthfulness** - Replaced mock analytics keyword output with database-backed aggregation from `TrendSignal` plus `Trend` fallback queries.

## Verification Notes

- Passed: targeted backend `pytest` for analytics, auth, gateway, and trend ingestion slices.
- Passed: frontend TypeScript check in `client/`.
- Passed: focused frontend Jest coverage for homepage live trends, trend service transport, and user quota UI.
- Not run: `next build` in this sweep.

## Instructions to Agents

Use `docs/roadmap.md` as the primary planning artifact. Update this file whenever code changes materially alter the verified state, blockers, or next delivery slice.
