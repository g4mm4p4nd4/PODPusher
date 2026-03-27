# PODPusher Delivery Roadmap

Last updated: March 27, 2026 (America/New_York)
Owner: PODPusher Coordinator (`podpusher-delivery`)

## Coordination Objective

Run a four-lane board with exactly one active slice per lane and explicit dependency gates:

1. `backend`
2. `frontend`
3. `platform-qa`
4. `integrations`

## Automation Control State

The automation layer is active because the live mainline audit is clean. Product
lane assignments below remain the authoritative backlog, but any future pause
still depends on `mainline-audit` reporting active newer-than-main drift or a
`main` checkout conflict. See [docs/automation_control_plane.md](./automation_control_plane.md)
for the shared resume contract.

Ordering rationale:
- Backend auth/identity behavior must stay stable before frontend removes any remaining fallback assumptions.
- Platform-QA workflow contract must stay aligned before integrations claims credential-backed smoke evidence.
- Integrations and Platform-QA both depend on external staging secret ownership and a manual workflow dispatch owner.

## Four-Lane Ready Board

| Lane | State | Ready Slice | Explicit File Boundaries | Dependency Gate | Verification Checks |
| --- | --- | --- | --- | --- | --- |
| `backend` | `READY` | Enforce auth-derived identity behavior across protected paths and keep invalid-header handling explicit. | `services/common/auth.py`; `services/common/quotas.py`; `services/common/rate_limit.py`; `services/gateway/api.py`; `tests/test_auth.py`; `tests/test_gateway.py`; `tests/test_quota.py`; `tests/test_rate_limit_middleware.py` | None | `python -m pytest -q tests/test_auth.py tests/test_gateway.py tests/test_quota.py tests/test_rate_limit_middleware.py` |
| `frontend` | `BLOCKED` | Remove remaining default internal-user fallback behavior in shared transport and settings/oauth callsites. | `client/services/apiBase.ts`; `client/services/oauth.ts`; `client/components/SocialSettings.tsx`; `client/pages/settings.tsx`; `client/__tests__/SocialSettings.test.tsx`; `client/__tests__/oauthCallback.test.tsx`; `client/__tests__/settingsPage.test.tsx` | Wait for backend contract freeze to avoid mixed auth semantics. | `npm --prefix client test -- --runInBand __tests__/SocialSettings.test.tsx __tests__/oauthCallback.test.tsx __tests__/settingsPage.test.tsx`; `npm --prefix client run typecheck` |
| `platform-qa` | `BLOCKED` | Keep staging smoke workflow contract and artifact expectations aligned with live smoke behavior. | `.github/workflows/staging-smoke.yml`; `tests/test_staging_smoke_workflow_contract.py`; `tests/test_ci_workflow_contract.py`; `docs/platform_qa_staging_smoke.md` | Requires staging secrets owner and manual/authorized workflow dispatch owner. | `python -m pytest -q -s tests/test_staging_smoke_workflow_contract.py tests/test_ci_workflow_contract.py` |
| `integrations` | `BLOCKED` | Produce one credential-backed non-stub trend->idea->image->listing smoke evidence run. | `tests/test_staging_pipeline_smoke.py`; `tests/test_integration_service.py`; `tests/test_integration_api.py`; `docs/platform_qa_staging_smoke.md`; `.github/workflows/staging-smoke.yml` | Depends on Platform-QA contract alignment and external staging secrets/dispatch ownership. | `python -m pytest -q -s tests/test_staging_pipeline_smoke.py tests/test_integration_service.py tests/test_integration_api.py`; then manual/CI dispatch of `Staging Pipeline Smoke` with `staging-smoke-junit` artifact |

## Active External Blockers

- Staging smoke still requires confirmed ownership for repository secrets: `OPENAI_API_KEY`, `ETSY_CLIENT_ID`, `ETSY_ACCESS_TOKEN`, `ETSY_SHOP_ID`, `PRINTIFY_API_KEY`, `PRINTIFY_SHOP_ID`.
- A human/authorized operator is still required for first `workflow_dispatch` execution evidence.
- Some local environments still cannot run full billing collections due missing `stripe` dependency.
- Mainline convergence is frozen until `/mnt/d/Users/Bear/Documents/GitHub/PODPusher` frees `main` and the active newer-than-main branch `codex/backend-auth-identity` is either folded or explicitly blocked.

## Cross-Lane Conflict Risks

- Parallel backend/frontend edits in auth identity paths can reintroduce inconsistent fallback behavior.
- Parallel integrations/platform-qa edits can drift smoke workflow, docs, and test contract expectations.
- Detached worktree planner updates can silently diverge from mainline docs unless consolidated each sweep.
