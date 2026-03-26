#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


ORIGIN_RECONCILE_PROMPT = (
    "Run `./scripts/codex_wsl_tasks.sh origin-reconcile` from the repo root. "
    "This command fetches origin, refuses a no-op exit when newer-than-main "
    "branch/worktree drift still exists, fast-forwards local main from origin/main "
    "when possible, runs `./scripts/codex_wsl_tasks.sh mainline-verify` before any "
    "push, and only fast-forward pushes local main to origin/main when verification "
    "passes and the working tree is clean. If the command fails, open an inbox item "
    "with the exact failing step, outstanding branch/worktree drift, checks run, "
    "push status, and blockers."
)
ORIGIN_RECONCILE_RRULE = "FREQ=HOURLY;INTERVAL=1;BYMINUTE=55"
MAINLINE_SWEEP_PROMPT = (
    "Run `./scripts/codex_wsl_tasks.sh mainline-sweep --verify` from the repo "
    "root. This command fetches origin, fast-forwards local main to origin/main "
    "when possible, discovers newer-than-main tracked branches from active "
    "worktrees, and folds the top-level candidates into local main with "
    "`git merge --no-ff`. If the command fails, open an inbox item with the exact "
    "branch or detached candidate that blocked the sweep, any dirty-worktree path, "
    "verification run, and the remaining backlog. Do not push to origin; leave "
    "remote sync to the origin-reconcile automation."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Patch Codex home settings for the PODPusher WSL migration."
    )
    parser.add_argument(
        "--codex-home",
        default=None,
        help="Path to the shared Codex home. Defaults to $CODEX_HOME or ~/.codex.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the changes instead of printing the pending updates.",
    )
    return parser.parse_args()


def resolve_codex_home(raw_path: str | None) -> Path:
    if raw_path:
        return Path(raw_path).expanduser()

    env_value = os.environ.get("CODEX_HOME")
    if env_value:
        return Path(env_value).expanduser()

    return Path.home() / ".codex"


def toml_basic_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def replace_basic_string_field(text: str, key: str, value: str) -> str:
    pattern = re.compile(
        rf'^{re.escape(key)}\s*=\s*"(?:[^"\\]|\\.)*"\s*$',
        flags=re.MULTILINE,
    )
    replacement = f"{key} = {toml_basic_string(value)}"
    updated, count = pattern.subn(replacement, text, count=1)

    if count != 1:
        raise ValueError(f"Unable to update {key!r} in TOML content.")

    return updated


def update_global_state(path: Path) -> tuple[bool, str]:
    original = path.read_text(encoding="utf-8")
    payload = json.loads(original)
    state = payload.setdefault("electron-persisted-atom-state", {})
    changed = False

    if state.get("runCodexInWindowsSubsystemForLinux") is not True:
        state["runCodexInWindowsSubsystemForLinux"] = True
        changed = True

    if state.get("integratedTerminalShell") != "wsl":
        state["integratedTerminalShell"] = "wsl"
        changed = True

    if not changed:
        return False, original

    return True, json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def update_origin_reconcile(path: Path) -> tuple[bool, str]:
    original = path.read_text(encoding="utf-8")
    updated = replace_basic_string_field(original, "prompt", ORIGIN_RECONCILE_PROMPT)
    updated = replace_basic_string_field(updated, "rrule", ORIGIN_RECONCILE_RRULE)
    return updated != original, updated


def update_mainline_sweep(path: Path) -> tuple[bool, str]:
    original = path.read_text(encoding="utf-8")
    updated = replace_basic_string_field(original, "prompt", MAINLINE_SWEEP_PROMPT)
    return updated != original, updated


def main() -> int:
    args = parse_args()
    codex_home = resolve_codex_home(args.codex_home)

    global_state_path = codex_home / ".codex-global-state.json"
    origin_reconcile_path = (
        codex_home / "automations" / "origin-reconcile" / "automation.toml"
    )
    mainline_sweep_path = (
        codex_home / "automations" / "podpusher-mainline-sweep" / "automation.toml"
    )

    planned_changes: list[tuple[Path, str]] = []

    if global_state_path.exists():
        changed, serialized = update_global_state(global_state_path)
        if changed:
            planned_changes.append((global_state_path, serialized))
    else:
        print(f"Missing file: {global_state_path}", file=sys.stderr)

    if origin_reconcile_path.exists():
        changed, serialized = update_origin_reconcile(origin_reconcile_path)
        if changed:
            planned_changes.append((origin_reconcile_path, serialized))
    else:
        print(f"Missing file: {origin_reconcile_path}", file=sys.stderr)

    if mainline_sweep_path.exists():
        changed, serialized = update_mainline_sweep(mainline_sweep_path)
        if changed:
            planned_changes.append((mainline_sweep_path, serialized))
    else:
        print(f"Missing file: {mainline_sweep_path}", file=sys.stderr)

    if not planned_changes:
        print("No Codex WSL migration changes are required.")
        return 0

    if not args.apply:
        print("Pending Codex WSL migration updates:")
        for path, _ in planned_changes:
            print(f"- {path}")
        print("Re-run with --apply to write them.")
        return 0

    for path, serialized in planned_changes:
        path.write_text(serialized, encoding="utf-8")
        print(f"Updated {path}")

    print("Restart the Codex app and open a new thread to validate the WSL shell.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
