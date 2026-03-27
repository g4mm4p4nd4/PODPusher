# PODPusher Mainline Recovery Plan

Last updated: March 27, 2026 (America/New_York)
Owner: PODPusher Coordinator (`podpusher-delivery`)

## Objective

Restore unattended code delivery to `origin/main` by fixing the mainline control plane, not by weakening merge gates.

## Current Diagnosis

The delivery system is stalling for process reasons:

1. The repo already has a fail-closed mainline gate (`branch-gate`, `mainline-audit`, `mainline-sweep`, `origin-reconcile`), but the topology does not always satisfy the gate.
2. The current worktree fleet contains detached heads and preserved snapshots, which means useful work can exist without a named branch or PR path.
3. `mainline-sweep` and `origin-reconcile` are intentionally blocked when `main` is checked out elsewhere or when the audit reports active drift.
4. Status documents and control-plane notes can become stale if they are not refreshed from the live audit.
5. There is no dedicated, automated "merge cadence" watchdog that forces attention when no PRs or merges happen for too long.

The root problem is therefore not "missing code". It is "missing promotion discipline".

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
| Canonical integration lease | One clean worktree owns `main`; all other worktrees are branch-only or snapshot-only. | DevOps-Engineer, Project-Manager | Access to the active worktree fleet; ability to free the `main` checkout conflict. | `git worktree list`; `./scripts/codex_wsl_tasks.sh mainline-audit --json`; `./scripts/codex_wsl_tasks.sh branch-gate` | Only one canonical integration worktree is allowed to run sweep/reconcile; audit no longer reports a checkout conflict. |
| Branch-to-PR promotion | Every ready slice becomes a named branch and a draft or ready PR automatically. | Project-Manager, lane owners | GitHub auth for PR creation; branch naming convention; branch-gate discipline. | `./scripts/codex_wsl_tasks.sh branch-gate`; GitHub PR creation command or API call; PR checklist includes branch name and HEAD SHA. | No completed work remains trapped on detached HEAD; each promotable slice has a branch, PR, and owner. |
| Mainline sweep and reconcile | Local `main` folds eligible branches and fast-forward pushes to `origin/main`. | Project-Manager, DevOps-Engineer | Canonical integration lease; clean worktree; green verification ladder. | `./scripts/codex_wsl_tasks.sh mainline-sweep --verify`; `./scripts/codex_wsl_tasks.sh origin-reconcile` | Sweep and reconcile succeed from the canonical integration worktree without manual intervention. |
| Unattended watchdogs | Stalls are visible within minutes instead of days. | DevOps-Engineer | Metrics/logging target; automation runner schedule. | Scheduled `mainline-audit`; alert on no PR creation or no merge within threshold. | A stalled control plane triggers an alert and a structured stop record automatically. |
| Live docs sync | Human-readable docs always match the live mainline state. | Docs-Writer, Project-Manager | Live audit output; sweep/reconcile completion. | Refresh `status.md`, `docs/automation_control_plane.md`, `docs/roadmap.md`, and `docs/source_of_truth_integration.md` from the current audit snapshot. | Docs show the actual blocker state, the current resume order, and the active integration owner. |

## Execution Sequence

1. Inventory every active worktree and classify it as canonical, branch-backed, or snapshot-only.
2. Free or reassign any non-canonical `main` checkout so exactly one integration worktree owns the merge path.
3. Refresh the live audit snapshot and record the exact blocker state before any remediation.
4. Convert promotable detached work into named branches.
5. Auto-create PRs for those branches so completed work is visible and reviewable.
6. Run `./scripts/codex_wsl_tasks.sh mainline-sweep --verify` from the canonical integration worktree.
7. Run `./scripts/codex_wsl_tasks.sh origin-reconcile` only after the sweep and validation ladder pass.
8. Resume automation runners in the documented order once the audit is clean.
9. Keep the audit/watchdog running so the system fails visibly instead of silently stalling.

## Operational Rules

- Do not relax `require_main_available` or `require_no_active_drift`.
- Do not let a detached head be the only copy of promotable work.
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
- `mainline-audit` reports no active newer-than-main drift and no checkout conflict.
- Every ready slice has a named branch and a PR.
- `mainline-sweep --verify` passes.
- `origin-reconcile` passes or cleanly no-ops after verification.
- The automation control plane can run for 24 hours without a manual revisit.
- A merge-stall alert fires if no merge or PR creation happens within the agreed threshold.

## Immediate Next Actions

1. Re-run the live audit from the canonical integration worktree.
2. Promote any eligible detached work to named branches.
3. Create or reopen PRs for the promoted branches.
4. Run the sweep and reconcile commands from the canonical worktree.
5. Refresh the status and freeze documents from the live audit output.
6. Re-enable the paused runners only after the resume gates are met.
