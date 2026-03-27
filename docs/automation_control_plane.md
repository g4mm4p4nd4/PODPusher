# Automation Control Plane Freeze

## Purpose

This document is the single freeze/resume contract for PODPusher Codex automations.
It captures the live blocked state, the stop-record payload, and the conditions
required before any runner resumes.

## Current Live State

At the time of this update, `mainline-audit --json` reports:

- State: `FROZEN`
- local `main` at `e380c72891370bd6d1e7a17b51c908d451572ac3`
- `main` checked out elsewhere at `/mnt/d/Users/Bear/Documents/GitHub/PODPusher`
- active newer-than-main drift: `codex/backend-auth-identity` at
  `151e5301a96289bb21f78d623a56291fd7621a1d`
- older unmerged backlog:
  - `codex/recovery-snapshot-20260325` at `837e167acd8b984825ba734013bef228ceab0060`
  - `codex/recovery-local-recreate-pr70-20260326` at `c7b5000cc0e32d164ad3ed6ef6c667af27dc3902`

The automation status files were frozen to `PAUSED` for:

- `origin-reconcile`
- `podpusher-backend-lane`
- `podpusher-cleanup`
- `podpusher-coordinator`
- `podpusher-mainline-sweep`

Already paused definitions remain paused:

- `podpusher-frontend-lane`
- `podpusher-integrations-lane`
- `podpusher-platform-qa-lane`
- `skill-progression-map`
- `create-tmp-probe1-txt-with-the-text-ok1-and-stop`

## Freeze Rules

- A frozen run emits one structured stop record and exits instead of retrying the
  same failure.
- `mainline-audit --json` is the canonical live source of truth for branch drift,
  detached heads, and `main` checkout conflicts.
- Keep the guardrails in `scripts/mainline_tools.py` intact; do not weaken
  `require_main_available`, `require_no_active_drift`, or the clean-worktree
  checks.
- Do not run `mainline-sweep --verify` or `origin-reconcile` while the primary
  repo has `main` checked out.
- Do not resume a lane simply because a later retry timed out. Resume only after
  the live audit is clean.

## Resume Gates

1. `./scripts/codex_wsl_tasks.sh mainline-audit --json` shows no active
   newer-than-main drift and no `main` checkout conflict.
2. The intended integration worktree is clean and attached to a named `codex/*`
   branch.
3. `./scripts/codex_wsl_tasks.sh branch-gate` passes from that worktree.
4. `./scripts/codex_wsl_tasks.sh mainline-sweep --verify` succeeds.
5. `./scripts/codex_wsl_tasks.sh origin-reconcile` succeeds or no-ops only after
   the sweep is green.

## Resume Order

1. `podpusher-mainline-sweep`
2. `origin-reconcile`
3. `podpusher-coordinator`
4. `podpusher-backend-lane`
5. `podpusher-frontend-lane`
6. `podpusher-platform-qa-lane`
7. `podpusher-integrations-lane`
8. `podpusher-cleanup`

## Structured Stop Record

Every blocked run should report:

- automation id
- timestamp
- branch
- HEAD SHA
- blocker
- next owner action
- resume eligibility

## Operational Prompt

```text
Audit all PODPusher automations and treat the current condition as a control-plane deadlock, not a product-code failure.

1. Inventory every runnable automation definition and classify it as ACTIVE, PAUSED, BLOCKED, or READY.
2. Pause every active PODPusher runner until the mainline is clean and the integration authority is unambiguous.
3. Use `mainline-audit` as the only live source of truth for branch drift, checked-out `main`, and dirty worktrees.
4. Do not weaken `mainline_tools.py` guardrails; fix the workflow topology instead.
5. Require a dedicated clean integration worktree and a single lease/lock for `mainline-sweep --verify` and `origin-reconcile`.
6. Resume work-producing automations only after the active newer-than-main branch is folded and verified.
7. Report every run with one structured record: automation id, timestamp, branch, HEAD SHA, blocker, next owner action, and resume eligibility.
8. Keep backlog branches and scratch worktrees out of the active sweep path; triage them separately after the active drift is resolved.
9. Optimize for throughput by preventing retry loops, reducing duplicate runs, and making the coordinator the only resume authority.
```
