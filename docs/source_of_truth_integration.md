# Source-of-Truth Integration

## Purpose

This runbook defines how local work is reconciled with `origin/main`, which is the
system of record for the repository. The goal is not just to move commits
upstream, but to prove that local changes still behave correctly when replayed on
top of the current remote baseline.

## First Principles

1. `origin/main` is the source of truth. Local branches are proposed deltas.
2. A delta is not integration-ready until it is replayed onto the latest
   `origin/main` and the full validation ladder passes.
3. Integration must fail closed. If conflicts, broken builds, or failing checks
   appear, the process stops with a precise failure report instead of guessing.
4. The safest integration unit is an explicit commit sequence. Replaying commits
   makes conflicts and regressions attributable.
5. Automation must preserve user work. A dirty worktree is a stop condition, not
   something to "fix" automatically.

## Preconditions

- Git access to `origin`
- A clean working tree
- Known validation commands for backend, frontend, migrations, and e2e
- A non-`main` integration branch

If `git status --porcelain` is not empty, stop and either commit the work or move
it aside intentionally. Do not let automation stash or rewrite uncommitted work
without an explicit human instruction.

## Integration Algorithm

### 1. Refresh the source of truth

```bash
git fetch origin --prune
git rev-parse origin/main
```

This establishes the exact remote baseline being targeted.

### 2. Measure divergence

```bash
git rev-list --left-right --count origin/main...HEAD
git log --oneline --decorate origin/main..HEAD
git log --oneline --decorate HEAD..origin/main
```

Classify the result:

- `0 N`: local work has not been integrated upstream yet
- `N 0`: local branch is stale and must absorb upstream first
- `N M`: both sides moved and a true reconciliation is required

### 3. Rebuild integration from the source of truth

Start from the remote baseline, then replay the local delta onto it.

```bash
git checkout -b codex/integrate-<date> origin/main
git cherry-pick <commit-1> <commit-2> ...
```

Why this shape:

- It proves the branch can be reconstructed from `origin/main`
- It isolates conflicts to specific commits
- It avoids treating a stale local base as authoritative

For a private linear branch, `git rebase origin/main` is acceptable. For
automation, explicit replay is easier to audit.

### 4. Resolve failures by type

Every failure fits one of these buckets:

- Merge conflict: two edits touched the same lines or file structure
- Contract drift: one side changed an API, schema, translation key, route, or
  test assumption
- Build failure: types, imports, generated assets, or config no longer line up
- Runtime regression: tests compile but behavior changed
- Environment failure: missing dependency, locked file, bad path, bad secret, or
  nondeterministic setup

Handle them in that order. Text conflicts come first, then broken interfaces,
then proof of runtime behavior.

### 5. Run the validation ladder

Validation should go from cheapest to most system-wide:

```bash
flake8
python scripts/verify_translations.py
npx tsc --noEmit --project client/tsconfig.json
alembic upgrade head
pytest
npm test --prefix client -- --runInBand
npm run build --prefix client
npm exec --prefix client playwright -- test
```

Project-specific additions can be inserted, but the rule is stable:

1. Static checks first
2. Schema and migration correctness next
3. Service and unit behavior after that
4. Production build after code-level checks
5. Browser and workflow proof last

Any red step blocks integration. Do not skip laterally to merge anyway.

### 6. Push only proven state

Once the replayed branch is green:

```bash
git push -u origin codex/integrate-<date>
```

Then open a PR to `main`. The merge gate is:

- no unresolved conflicts
- local validation green
- remote CI green
- review complete

### 7. Merge and verify

After merge:

```bash
git fetch origin --prune
git rev-parse origin/main
git branch --merged origin/main
```

Confirm that the integration commit range is reachable from `origin/main`. Only
then is the work part of the source of truth.

## Automation Contract

An automation for this workflow should have the following shape.

### Inputs

- target remote branch, default `origin/main`
- candidate branch or explicit commit range
- ordered validation commands
- retry policy for flaky external steps

### Outputs

- integration branch name
- replayed commit range
- pass/fail result for each validation step
- conflict report when replay fails
- PR link or merge commit once completed

### Guardrails

- stop on dirty worktree
- never push directly to `main`
- never force-push without explicit approval
- never auto-resolve semantic conflicts without rerunning tests
- persist logs for each failed step

### Failure Policy

- Conflict during replay: stop, summarize conflicting files, require manual fix
- Static or build failure: stop, patch, rerun from the failed step and then the
  remainder of the ladder
- Test failure: fix the underlying contract or behavior, not the symptom
- Flaky external failure: retry bounded times, then mark as infrastructure noise
  and fail visibly

## Current Repository Snapshot

As exercised on March 6, 2026, this repository validated cleanly locally after
replaying and repairing the current integration branch. The branch can now be
treated as PR-ready once its remaining unpushed changes are committed and pushed
to `origin`.
