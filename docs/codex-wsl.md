# Codex WSL For PODPusher

This repo now ships a project-local Codex environment at `.codex/environments/environment.toml`. Codex prioritizes the default `environment.toml` name, so this file becomes the repo-scoped local environment for worktrees and the main checkout once the change is merged.

## Repo-local pieces

- `.codex/environments/environment.toml`
  - Registers a single Linux-first local environment named `podpusher-wsl`.
  - Uses `./scripts/codex_wsl_tasks.sh bootstrap` as the worktree setup command.
  - Exposes toolbar actions for bootstrap, backend tests, frontend tests, frontend build, Docker Compose, the Celery worker, and a repo-local Codex CLI entrypoint.
- `scripts/codex_wsl_env.sh`
  - Exports the shared WSL defaults for `CODEX_HOME`, Python and npm caches, the Linux-only virtualenv path, and the repo-local Codex CLI install path.
- `scripts/codex_wsl_tasks.sh`
  - Centralizes the Linux-first bootstrap and task entrypoints used by the local environment.
  - Keeps the Python venv separate from the existing Windows `.codex-venv` by using `.codex-venv-wsl`.
  - Installs dependencies only when `requirements.txt` or the frontend manifest changes.
  - Exposes `branch-gate`, `mainline-audit`, `mainline-sweep`, `mainline-verify`, and `origin-reconcile` as repo-owned convergence commands.
- `scripts/apply_codex_wsl_migration.py`
  - Patches the writable-outside-repo Codex home when you run it manually with access to `%USERPROFILE%\.codex`.
  - Sets the app state toggles that matter for WSL and rewrites the active mainline automations so they use the repo's WSL-first verification flow.

## WSL usage

Run these from WSL inside the repo:

```bash
./scripts/codex_wsl_tasks.sh bootstrap
./scripts/codex_wsl_tasks.sh backend-test
./scripts/codex_wsl_tasks.sh frontend-build
./scripts/codex_wsl_tasks.sh frontend-test
./scripts/codex_wsl_tasks.sh mainline-verify
./scripts/codex_wsl_tasks.sh mainline-audit
./scripts/codex_wsl_tasks.sh compose-config
```

## Continuous mainline flow

The intended automation order is:

1. Work-producing automations start from `./scripts/codex_wsl_tasks.sh branch-gate`, create or update a named branch, and report branch name plus `HEAD` SHA in their inbox handoff.
2. `podpusher-mainline-sweep` runs `./scripts/codex_wsl_tasks.sh mainline-sweep --verify`, which discovers newer-than-main tracked branches from active worktrees and folds only the top-level candidates into local `main` with `git merge --no-ff`.
3. `origin-reconcile` runs `./scripts/codex_wsl_tasks.sh origin-reconcile`, which refuses a no-op exit while newer-than-main drift still exists, runs `./scripts/codex_wsl_tasks.sh mainline-verify` before any push, and only then fast-forward pushes local `main` to `origin/main`.
4. A run is not complete until the delta is either reachable from `origin/main` or explicitly reported as blocked with branch name, `HEAD` SHA, and reason.

`mainline-verify` does not install dependencies. It only validates against the repo-local WSL toolchains that are already present, so missing toolchains fail closed instead of silently pushing an unverified `main`.

To install a repo-local Codex CLI into the workspace instead of your WSL home:

```bash
./scripts/codex_wsl_tasks.sh install-cli
./scripts/codex_wsl_tasks.sh codex --help
```

## External Codex home changes

This session cannot directly edit `%USERPROFILE%\.codex` because those files are outside the writable root. The migration helper is ready for when you run it from a shell with access to your Codex home:

```bash
python3 scripts/apply_codex_wsl_migration.py --apply --codex-home /mnt/c/Users/Bear/.codex
```

That script currently:

- Forces `runCodexInWindowsSubsystemForLinux = true` in `.codex-global-state.json`
- Forces `integratedTerminalShell = "wsl"` in `.codex-global-state.json`
  - Rewrites `automations/origin-reconcile/automation.toml` to call the repo-owned `origin-reconcile` command
  - Rewrites `automations/podpusher-mainline-sweep/automation.toml` to call the repo-owned `mainline-sweep --verify` command

## Shell startup

For native WSL CLI usage outside this repo, keep `CODEX_HOME` shared with the Windows app:

```bash
echo 'export CODEX_HOME=/mnt/c/Users/Bear/.codex' >> ~/.bashrc
```

If you want a global WSL Codex CLI instead of the repo-local install, the official Codex CLI docs use:

```bash
npm install -g @openai/codex@latest
```

## Validation checklist

After merging this repo change and applying the external migration:

1. Restart the Codex app.
2. Open a brand-new thread and confirm the shell reports WSL rather than PowerShell.
3. Confirm the working directory resolves under `/mnt/c/...` or `/mnt/d/...`.
4. Run `./scripts/codex_wsl_tasks.sh print-env` from WSL and verify `CODEX_HOME` points at `/mnt/c/Users/Bear/.codex`.
5. Run the bootstrap, backend, frontend, and compose validation commands above.
