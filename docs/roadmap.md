# PODPusher Delivery Roadmap

Last updated: March 6, 2026

## Project Stage

PODPusher is currently a late Phase 0 prototype with selected Phase 1 features present. The core architecture exists, and the main workspace now includes the previously detached automation output for gateway/client transport, live trend dashboard flows, analytics aggregation, and OAuth API hardening. Internal rollout readiness still depends on trustworthy bootstraps, CI coverage, and one credential-backed end-to-end validation path.

## Verified Findings

### P0 Flow Restoration

- Resolved in code: restored the missing shared client API base module via `client/services/apiBase.ts`.
- Resolved in code: wired shared authenticated headers into the frontend paths that were failing in practice, including OAuth, `/generate`, quota, and notifications.
- Resolved in code: exposed `/api/user/*` and `/api/analytics` through the gateway.
- Resolved in code: fixed the invalid gateway lifespan declaration by converting it to an async lifespan function.
- Verified locally: targeted backend pytest now passes for the analytics, auth, gateway, and trend-ingestion slices.

### P1 Internal Rollout Readiness

- Resolved in code: replaced static analytics keyword output with aggregated `TrendSignal` data and `Trend` fallback queries.
- Resolved in code: live trend refresh now returns telemetry, exposes `/api/trends/live/status`, and supports category/source/recency/limit filters.
- Resolved in code: homepage now consumes live trend APIs with refresh, loading/error/empty states, and focused test coverage.
- Pending: replace the empty Alembic baseline with an authoritative clean-bootstrap migration and strengthen migration assertions beyond one table/index.
- Pending: align `.env.example`, Docker, and docs with the Etsy OAuth credential model actually required by the integration code.
- Pending: add frontend build and type-check coverage to CI so compile failures are caught before merge.
- Pending: validate one non-stub trend -> idea -> image -> listing staging path when credentials are available.

### P2 Cleanup

- Pending: remove unresolved merge artifacts from `README.md` and `docs/internal_docs.md`.
- Pending: remove remaining hardcoded internal-user assumptions where they still block multi-user internal testing.
- Pending: finish the remaining i18n rollout across less-covered frontend flows.
- Pending: keep detached automation worktrees from accumulating by sweeping/merging them on an hourly cadence.

## Ordered Milestones

1. **Buildable and callable UI**
   - Status: restored and verified with focused frontend Jest plus TypeScript checks.
2. **Trustworthy bootstraps and CI**
   - Scope: Alembic baseline, env/runtime contract alignment, frontend build plus type-check in CI.
3. **Real trend-to-listing path**
   - Scope: credential-backed live ingestion, OpenAI path validation, and Printify/Etsy staging smoke coverage.
4. **Cleanup and rollout polish**
   - Scope: docs cleanup, multi-user follow-through, i18n completion, and automation/worktree hygiene.

## Current Slice

Complete the remaining internal-rollout prerequisites for Milestone 2:

- Make the baseline migration authoritative for a clean database bootstrap.
- Update runtime configuration docs and Docker envs to use the real Etsy OAuth contract.
- Extend CI to run frontend type-check and build, not just Jest.

## Verification Snapshot

- Passed: `python -m pytest tests/test_analytics.py tests/test_auth.py tests/test_gateway.py tests/test_trend_ingestion_api.py tests/test_trend_ingestion_service.py tests/test_trend_ingestion_utils.py`
- Passed: `npx tsc --noEmit --project client/tsconfig.json`
- Passed: `npm test --prefix client -- --runInBand __tests__/index.test.tsx __tests__/trendsService.test.ts __tests__/UserQuota.test.tsx`
- Not run: `next build`

## Next Slice

Implement the migration and CI hardening work, then re-run validation in an environment with the frontend production build enabled and credential-backed staging access for Etsy, Printify, Stripe, and OpenAI.
