# Changelog

## Unreleased
- Realigned local `main` with `origin/main` after the project pause, confirmed the quota and image-review slices are already present on main, and refreshed the control-plane docs around the live `3e890f8` baseline with only the two preserved recovery branches left for manual triage.
- Added an hourly `podpusher-mainline-watchdog` automation and refreshed the automation control-plane snapshot so stalls surface as inbox items instead of going silent.
- Excluded repo-local virtualenv and Node toolchain directories from flake8 so `mainline-verify` no longer linted vendored dependencies.
- Refreshed the mainline control-plane docs from the live git state, cleared the obsolete freeze snapshot, and optimized `mainline-audit` to avoid scanning every worktree status on each run.
- Added `planning.md` as the root-level mainline recovery backlog so the control-plane remediation work is tracked in one executable place.
- Froze the active PODPusher automation runners, captured the then-current mainline deadlock in `docs/automation_control_plane.md`, and refreshed the live mainline/status docs from `mainline-audit`.
- Added a fail-closed `./scripts/codex_wsl_tasks.sh mainline-verify` command so `origin-reconcile` can validate backend, frontend, build, migrations, and Playwright gates before pushing `main`.
- Documented the continuous local-main automation flow and updated the WSL migration helper to preserve commit traceability during mainline folding.
- Added repo-owned `branch-gate`, `mainline-audit`, `mainline-sweep`, and `origin-reconcile` commands so automations can enforce tracked-branch handoff, consume newer-than-main drift, and refuse false no-op reconciliation.
- Removed stale merge separator artifacts from the primary docs runbooks.
- Removed notifications payload `user_id` overrides and now enforce authenticated-request ownership for immediate and scheduled notification creation.
- Hardened common auth resolution so invalid/malformed `Authorization` headers no longer fall back to `X-User-Id`, with focused dependency tests for `require_user_id` and `optional_user_id`.
- Localized `ErrorBoundary` copy via i18n keys (`errorBoundary.*`) and added focused component coverage for translated fallback and retry recovery behavior.
- Updated staging smoke to pass explicit env-backed Printify/Etsy credential payloads to live integration calls.
- Added internationalization with English and Spanish translations.
- New language switcher allows changing locale in the dashboard.
- Replaced analytics mock keyword feed with live aggregation from trend ingestion data (`TrendSignal`) plus `Trend` fallback, with validated query bounds and expanded backend tests.
- Hardened live integration validation for Printify and Etsy: live mode now accepts env-backed shop IDs, rejects missing live identifiers, and includes focused service/API test coverage.
- Added trend source provenance (`live` vs `fallback`) to trend scraper outputs and tightened staging smoke to fail when fallback trend seeds are used.
- Removed hardcoded billing webhook ownership fallback (`user_id=1`) by resolving subscription ownership from metadata or `cus_stub_<user_id>` and added focused billing tests for stub-path ownership mapping.
- Removed header-only auth assumption in quota and gateway rate-limit middleware by resolving Bearer session user IDs, with new focused tests for authenticated middleware behavior.
- Unified image quota middleware auth resolution with shared `require_user_id`, so invalid bearer tokens no longer degrade to misleading `Missing X-User-Id` errors; added focused gateway/quota auth precedence tests.
- Removed header-only auth assumption in notifications API by resolving Bearer session user IDs with `X-User-Id` fallback, plus focused notification auth tests.
