# PODPusher Mainline Recovery Plan

Last updated: April 5, 2026 (America/New_York)
Owner: PODPusher Coordinator (`podpusher-delivery`)

## Objective

Resume unattended code delivery from the current remote baseline by keeping
`main` aligned with `origin/main` and moving stale recovery branches out of the
critical path.

## Current Diagnosis

The delivery system is now restartable, but the control plane still needs
housekeeping discipline:

1. The repo already has a fail-closed mainline gate (`branch-gate`, `mainline-audit`, `mainline-sweep`, `origin-reconcile`), and local `main` now matches `origin/main` at `3e890f8`.
2. The worktree fleet still contains many detached archival copies plus this maintenance checkout at older commit `e380c72`, so restart ownership is still easy to blur.
3. Two preserved recovery branches remain intentionally outside the sweep path until they are either archived or promoted deliberately.
4. Status documents and control-plane notes become stale quickly if they are not refreshed from the live audit after a pause.
5. The hourly watchdog exists, but human restart ownership is still required before merge-oriented automation resumes.

The root problem is therefore no longer "missing code". It is "clean restart ownership".

## Recovery Principles

- Keep the guardrails in `scripts/mainline_tools.py` intact.
- Fix the worktree and branch topology so the guardrails can pass.
- Every completed slice must have a named branch and a PR path.
- Detached work may be preserved as a snapshot, but it must not remain the only copy of promotable work.
- `mainline-sweep` and `origin-reconcile` must remain the only paths to `main`.
- Any blocked run must stop once, emit a structured blocker, and not spin in retry loops.

## Workstreams

| Workstream | Outcome | Owner | Dependencies | Verification | Exit Criteria |
| --- | --- | --- | --- | --- | --- |
| Canonical integration lease | One clean worktree owns `main`; detached archival copies stay out of the merge path. | DevOps-Engineer, Project-Manager | Access to the active worktree fleet; ability to start from a clean `main`-attached checkout. | `git worktree list`; `./scripts/codex_wsl_tasks.sh mainline-audit --json`; `./scripts/codex_wsl_tasks.sh branch-gate` | One integration worktree is clearly designated for sweep/reconcile; detached archival copies are documented as non-authoritative. |
| Recovery branch triage | The two preserved recovery branches are either archived as obsolete or promoted intentionally. | Project-Manager, lane owners | Semantic diff review; branch naming convention; branch-gate discipline if replay is needed. | `git log --oneline main..codex/recovery-*`; focused tests for any replayed slice; PR creation if promoted. | No preserved recovery branch remains ambiguous about whether it is backlog, replay, or archive-only history. |
| Mainline verification and reconcile | Local `main` stays aligned with `origin/main`; sweep/reconcile run only when new tracked drift appears. | Project-Manager, DevOps-Engineer | Canonical integration lease; clean worktree; green verification ladder. | `./scripts/codex_wsl_tasks.sh mainline-sweep --verify`; `./scripts/codex_wsl_tasks.sh origin-reconcile` | Sweep/reconcile remain green and fail-closed without trying to consume archival detached worktrees. |
| Unattended watchdogs | Stalls are visible within minutes instead of days. | DevOps-Engineer | Metrics/logging target; automation runner schedule. | Scheduled `mainline-audit`; alert on no PR creation or no merge within threshold. | A stalled control plane triggers an alert and a structured stop record automatically. |
| Live docs sync | Human-readable docs always match the live mainline state. | Docs-Writer, Project-Manager | Live audit output; sweep/reconcile completion. | Refresh `status.md`, `docs/automation_control_plane.md`, `docs/roadmap.md`, and `docs/source_of_truth_integration.md` from the current audit snapshot. | Docs show the actual blocker state, the current resume order, and the active integration owner. |

## Execution Sequence

1. Align local `main` with `origin/main` and capture the fresh audit snapshot.
2. Pick one clean worktree attached to `main` as the canonical integration lease.
3. Classify detached worktrees at or behind `main` as archival unless they show new semantic drift.
4. Triage the two preserved recovery branches and decide whether they are archive-only or promotion candidates.
5. Run `./scripts/codex_wsl_tasks.sh mainline-sweep --verify` and `./scripts/codex_wsl_tasks.sh origin-reconcile` only from the canonical integration worktree when new tracked drift appears.
6. Resume automation runners in the documented order once the audit is clean and the integration lease is explicit.
7. Keep the audit/watchdog running so the system fails visibly instead of silently stalling.

## Operational Rules

- Do not relax `require_main_available` or `require_no_active_drift`.
- Do not let a detached head or archival worktree become the accidental source of new production work.
- Do not allow multiple runners to contend for the same `main` checkout.
- Do not treat "no PRs" as acceptable if ready work exists.
- Do not merge without the verification ladder succeeding.
- Do not let status docs drift away from the live audit snapshot.

## Automation Contract

Each automation run should emit these fields before exit:

- automation id
- timestamp
- branch name
- HEAD SHA
- blocker, if any
- next owner action
- resume eligibility

If any of those fields are missing, the run is not ready for unattended operation.

## Success Criteria

- One canonical integration worktree owns `main`.
- local `main` matches `origin/main`.
- `mainline-audit` reports no active newer-than-main drift and no checkout conflict.
- Every ready slice has a named branch and a PR.
- `mainline-sweep --verify` passes.
- `origin-reconcile` passes or cleanly no-ops after verification.
- The automation control plane can run for 24 hours without a manual revisit.
- A merge-stall alert fires if no merge or PR creation happens within the agreed threshold.

## Immediate Next Actions

1. Start a clean `main`-attached integration worktree for active delivery.
2. Re-run the live audit from that worktree and confirm no new tracked drift appears.
3. Decide whether the two preserved recovery branches are archive-only or need deliberate replay.
4. Run the backend auth/quota verification slice before reopening frontend work.
5. Refresh the status and control-plane documents from the live audit output whenever the baseline moves again.
6. Re-enable the paused runners only after the resume gates are met.
