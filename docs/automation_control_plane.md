# Automation Control Plane

## Purpose

This document is the single state/resume contract for PODPusher Codex automations.
It captures the live mainline state, the stop-record payload, and the conditions
required before any runner resumes.

## Current Live State

At the time of this update, `mainline-audit --json` reports:

- State: `ACTIVE`
- local `main` at `1d3ed67...`
- `origin/main` matches local `main`
- canonical integration worktree: `/mnt/d/Users/Bear/.codex-data/worktrees/c0b6/PODPusher`
- no active newer-than-main drift
- older unmerged backlog:
  - `codex/recovery-snapshot-20260325` at `837e167acd8b984825ba734013bef228ceab0060`
  - `codex/recovery-local-recreate-pr70-20260326` at `c7b5000cc0e32d164ad3ed6ef6c667af27dc3902`
- always-on watchdog: `podpusher-mainline-watchdog` runs hourly as a read-only stall detector and opens an inbox note on clean or stalled snapshots.

The repo-owned mainline is not frozen. Work-producing automations may proceed
as long as they keep the live audit clean.

## Operating Rules

- A run emits one structured stop record and exits instead of retrying the same failure.
- `mainline-audit --json` is the canonical live source of truth for branch drift,
  detached heads, and `main` checkout conflicts.
- `podpusher-mainline-watchdog` stays ACTIVE as a read-only monitor; it reports
  stalls and never mutates the repo.
- Keep the guardrails in `scripts/mainline_tools.py` intact; do not weaken
  `require_main_available`, `require_no_active_drift`, or the clean-worktree
  checks.
- Do not run `mainline-sweep --verify` or `origin-reconcile` from a dirty worktree.
- Do not retry a blocked run unless the blocker changed or was cleared.

## Resume Gates

1. `./scripts/codex_wsl_tasks.sh mainline-audit --json` shows no active
   newer-than-main drift and no `main` checkout conflict.
2. The intended integration worktree is clean and attached to a named `codex/*`
   branch.
3. `./scripts/codex_wsl_tasks.sh branch-gate` passes from that worktree.
4. `./scripts/codex_wsl_tasks.sh mainline-sweep --verify` succeeds.
5. `./scripts/codex_wsl_tasks.sh origin-reconcile` succeeds or no-ops only after
   the sweep is green.

## Always-On Monitor

`podpusher-mainline-watchdog` stays ACTIVE at all times and should keep running
even when merge-oriented lanes are paused. Its job is to surface stalls early,
not to repair them.

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
Audit all PODPusher automations and treat any future deadlock as a control-plane incident, not a product-code failure.

1. Inventory every runnable automation definition and classify it as ACTIVE, PAUSED, BLOCKED, or READY.
2. Pause active runners only when the live mainline audit reports drift or a checkout conflict.
3. Use `mainline-audit` as the only live source of truth for branch drift, checked-out `main`, and dirty worktrees.
4. Do not weaken `mainline_tools.py` guardrails; fix the workflow topology instead.
5. Require a dedicated clean integration worktree and a single lease/lock for `mainline-sweep --verify` and `origin-reconcile`.
6. Resume work-producing automations only after the active newer-than-main branch is folded and verified.
7. Report every run with one structured record: automation id, timestamp, branch, HEAD SHA, blocker, next owner action, and resume eligibility.
8. Keep backlog branches and scratch worktrees out of the active sweep path; triage them separately after the active drift is resolved.
9. Optimize for throughput by preventing retry loops, reducing duplicate runs, and making the coordinator the only resume authority.
```
