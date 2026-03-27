#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_ALLOWED_UNTRACKED = (
    "automation/",
    "scripts/automation/",
)


class MainlineError(RuntimeError):
    pass


@dataclass
class DirtyEntry:
    status: str
    path: str


@dataclass
class WorktreeState:
    path: str
    head: str
    branch: str | None
    dirty: list[DirtyEntry]


@dataclass
class BranchState:
    name: str
    sha: str
    subject: str
    commit_epoch: int
    ahead_of_main: int
    checked_out_paths: list[str]
    active: bool
    newer_than_main: bool


@dataclass
class DetachedCandidate:
    path: str
    sha: str
    subject: str
    commit_epoch: int
    newer_than_main: bool


def run(
    command: list[str], *, cwd: Path, check: bool = True
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        detail = stderr or stdout or "command failed"
        raise MainlineError(f"{' '.join(command)}: {detail}")
    return result


def git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=repo_root, check=check)


def repo_root_from(path: Path) -> Path:
    root = git(path, "rev-parse", "--show-toplevel").stdout.strip()
    return Path(root)


def current_branch(repo_root: Path) -> str | None:
    result = git(repo_root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def head_sha(repo_root: Path) -> str:
    return git(repo_root, "rev-parse", "HEAD").stdout.strip()


def commit_epoch(repo_root: Path, ref: str) -> int:
    return int(git(repo_root, "show", "-s", "--format=%ct", ref).stdout.strip())


def subject(repo_root: Path, ref: str) -> str:
    return git(repo_root, "show", "-s", "--format=%s", ref).stdout.strip()


def ref_exists(repo_root: Path, ref: str) -> bool:
    return git(repo_root, "rev-parse", "--verify", "--quiet", ref, check=False).returncode == 0


def is_ancestor(repo_root: Path, older: str, newer: str) -> bool:
    return (
        git(repo_root, "merge-base", "--is-ancestor", older, newer, check=False).returncode
        == 0
    )


def ahead_of_main(repo_root: Path, main_branch: str, ref: str) -> int:
    return int(
        git(
            repo_root,
            "rev-list",
            "--right-only",
            "--count",
            f"{main_branch}...{ref}",
        ).stdout.strip()
    )


def split_porcelain_entry(line: str) -> DirtyEntry:
    if not line:
        return DirtyEntry(status="", path="")
    status = line[:2]
    path = line[3:] if len(line) > 3 else ""
    return DirtyEntry(status=status, path=path)


def is_allowed_untracked(path: str, allowed_untracked: Iterable[str]) -> bool:
    normalized = path.strip()
    for prefix in allowed_untracked:
        clean_prefix = prefix.rstrip("/")
        if normalized == clean_prefix or normalized.startswith(f"{clean_prefix}/"):
            return True
    return False


def dirty_entries_for(
    worktree_path: Path, *, allowed_untracked: Iterable[str]
) -> list[DirtyEntry]:
    status_output = git(
        worktree_path, "status", "--porcelain=v1", "--untracked-files=all"
    ).stdout.splitlines()
    dirty: list[DirtyEntry] = []
    for line in status_output:
        entry = split_porcelain_entry(line)
        if entry.status == "??" and is_allowed_untracked(entry.path, allowed_untracked):
            continue
        dirty.append(entry)
    return dirty


def parse_worktrees(
    repo_root: Path,
    allowed_untracked: Iterable[str],
    dirty_paths: Iterable[Path] | None = None,
) -> list[WorktreeState]:
    # Scanning every worktree status is expensive on this repo. Restrict the
    # dirt check to the paths we actually need for audit and gate decisions.
    dirty_targets = {Path(path) for path in dirty_paths} if dirty_paths is not None else {repo_root}
    output = git(repo_root, "worktree", "list", "--porcelain").stdout.splitlines()
    records: list[dict[str, str | bool]] = []
    current: dict[str, str | bool] = {}
    for line in [*output, ""]:
        if not line:
            if current:
                records.append(current)
            current = {}
            continue
        key, _, value = line.partition(" ")
        if key in {"worktree", "HEAD", "branch"}:
            current[key] = value
        elif key == "detached":
            current[key] = True

    worktrees: list[WorktreeState] = []
    for record in records:
        worktree_path = Path(str(record["worktree"]))
        branch_name: str | None = None
        if "branch" in record:
            branch_name = str(record["branch"]).removeprefix("refs/heads/")
        worktrees.append(
            WorktreeState(
                path=str(worktree_path),
                head=str(record["HEAD"]),
                branch=branch_name,
                dirty=(
                    dirty_entries_for(
                        worktree_path,
                        allowed_untracked=allowed_untracked,
                    )
                    if worktree_path in dirty_targets
                    else []
                ),
            )
        )
    return worktrees


def collect_branches(
    repo_root: Path,
    *,
    main_branch: str,
    main_epoch: int,
    worktrees: list[WorktreeState],
) -> list[BranchState]:
    by_branch: dict[str, list[str]] = {}
    for worktree in worktrees:
        if worktree.branch:
            by_branch.setdefault(worktree.branch, []).append(worktree.path)

    branch_lines = git(
        repo_root,
        "for-each-ref",
        "--format=%(refname:short)\t%(objectname)\t%(subject)\t%(committerdate:unix)",
        "refs/heads",
    ).stdout.splitlines()
    branches: list[BranchState] = []
    for line in branch_lines:
        name, sha, branch_subject, branch_epoch = line.split("\t", maxsplit=3)
        if name == main_branch:
            continue
        tip_epoch = int(branch_epoch)
        branches.append(
            BranchState(
                name=name,
                sha=sha,
                subject=branch_subject,
                commit_epoch=tip_epoch,
                ahead_of_main=ahead_of_main(repo_root, main_branch, name),
                checked_out_paths=sorted(by_branch.get(name, [])),
                active=name in by_branch,
                newer_than_main=tip_epoch > main_epoch,
            )
        )
    return branches


def collect_detached_candidates(
    repo_root: Path,
    *,
    main_branch: str,
    main_sha: str,
    main_epoch: int,
    worktrees: list[WorktreeState],
) -> list[DetachedCandidate]:
    detached: list[DetachedCandidate] = []
    for worktree in worktrees:
        if worktree.branch is not None or worktree.head == main_sha:
            continue
        if is_ancestor(repo_root, worktree.head, main_branch):
            continue
        tip_epoch = commit_epoch(repo_root, worktree.head)
        detached.append(
            DetachedCandidate(
                path=worktree.path,
                sha=worktree.head,
                subject=subject(repo_root, worktree.head),
                commit_epoch=tip_epoch,
                newer_than_main=tip_epoch > main_epoch,
            )
        )
    return detached


def collapse_branches(repo_root: Path, branches: list[BranchState]) -> list[BranchState]:
    collapsed: list[BranchState] = []
    for candidate in branches:
        if candidate.ahead_of_main <= 0:
            continue
        shadowed = False
        for other in branches:
            if candidate.name == other.name or other.ahead_of_main <= 0:
                continue
            if is_ancestor(repo_root, candidate.name, other.name):
                shadowed = True
                break
        if not shadowed:
            collapsed.append(candidate)
    return sorted(collapsed, key=lambda branch: (branch.commit_epoch, branch.name))


def main_checked_out_elsewhere(
    repo_root: Path, *, current_root: Path, worktrees: list[WorktreeState], main_branch: str
) -> str | None:
    for worktree in worktrees:
        if worktree.branch == main_branch and Path(worktree.path) != current_root:
            return worktree.path
    return None


def build_audit(
    repo_root: Path, *, main_branch: str, remote_main: str, allowed_untracked: Iterable[str]
) -> dict[str, object]:
    current_root = repo_root_from(repo_root)
    current_head = head_sha(current_root)
    current_ref = current_branch(current_root)
    main_sha = git(current_root, "rev-parse", main_branch).stdout.strip()
    main_epoch = commit_epoch(current_root, main_branch)
    worktrees = parse_worktrees(
        current_root,
        allowed_untracked,
        dirty_paths={current_root},
    )
    branches = collect_branches(
        current_root,
        main_branch=main_branch,
        main_epoch=main_epoch,
        worktrees=worktrees,
    )
    detached = collect_detached_candidates(
        current_root,
        main_branch=main_branch,
        main_sha=main_sha,
        main_epoch=main_epoch,
        worktrees=worktrees,
    )
    top_level_branches = collapse_branches(
        current_root,
        [branch for branch in branches if branch.newer_than_main],
    )
    backlog_branches = sorted(
        [
            branch
            for branch in branches
            if branch.ahead_of_main > 0 and not branch.newer_than_main
        ],
        key=lambda branch: (branch.commit_epoch, branch.name),
    )

    current_worktree_state = next(
        worktree for worktree in worktrees if Path(worktree.path) == current_root
    )

    return {
        "repo_root": str(current_root),
        "current_head": current_head,
        "current_branch": current_ref,
        "main": {
            "branch": main_branch,
            "sha": main_sha,
            "commit_epoch": main_epoch,
            "subject": subject(current_root, main_branch),
        },
        "remote_main": remote_main,
        "current_worktree": asdict(current_worktree_state),
        "worktrees": [asdict(worktree) for worktree in worktrees],
        "active_newer_than_main": {
            "branches": [asdict(branch) for branch in top_level_branches],
            "detached": [
                asdict(candidate)
                for candidate in detached
                if candidate.newer_than_main
            ],
        },
        "older_unmerged_backlog": [asdict(branch) for branch in backlog_branches],
        "main_checked_out_elsewhere": main_checked_out_elsewhere(
            current_root,
            current_root=current_root,
            worktrees=worktrees,
            main_branch=main_branch,
        ),
    }


def format_dirty(entries: list[DirtyEntry]) -> str:
    return ", ".join(f"{entry.status} {entry.path}" for entry in entries)


def print_audit(audit: dict[str, object]) -> None:
    print(f"Repo: {audit['repo_root']}")
    current_branch_name = audit["current_branch"] or "detached"
    print(f"Current HEAD: {audit['current_head']} ({current_branch_name})")
    main = audit["main"]
    assert isinstance(main, dict)
    print(f"Main: {main['branch']} @ {main['sha']}")

    current_worktree = audit["current_worktree"]
    assert isinstance(current_worktree, dict)
    dirty = current_worktree["dirty"]
    if dirty:
        print("Current worktree has disallowed dirt:")
        for entry in dirty:
            print(f"- {entry['status']} {entry['path']}")
    else:
        print("Current worktree is clean.")

    active = audit["active_newer_than_main"]
    assert isinstance(active, dict)
    active_branches = active["branches"]
    active_detached = active["detached"]
    if active_branches or active_detached:
        print("Newer-than-main active drift:")
        for branch in active_branches:
            print(
                "- branch {name} @ {sha} (+{ahead_of_main}) [{paths}] {subject}".format(
                    name=branch["name"],
                    sha=branch["sha"],
                    ahead_of_main=branch["ahead_of_main"],
                    paths=", ".join(branch["checked_out_paths"]) or "not checked out",
                    subject=branch["subject"],
                )
            )
        for candidate in active_detached:
            print(
                "- detached {path} @ {sha} {subject}".format(
                    path=candidate["path"],
                    sha=candidate["sha"],
                    subject=candidate["subject"],
                )
            )
    else:
        print("No newer-than-main active drift found.")

    backlog = audit["older_unmerged_backlog"]
    assert isinstance(backlog, list)
    if backlog:
        print("Older unmerged backlog:")
        for branch in backlog:
            print(
                "- branch {name} @ {sha} (+{ahead_of_main}) {subject}".format(
                    name=branch["name"],
                    sha=branch["sha"],
                    ahead_of_main=branch["ahead_of_main"],
                    subject=branch["subject"],
                )
            )


def require_clean_current_worktree(audit: dict[str, object]) -> None:
    current_worktree = audit["current_worktree"]
    assert isinstance(current_worktree, dict)
    dirty = [
        DirtyEntry(status=str(entry["status"]), path=str(entry["path"]))
        for entry in current_worktree["dirty"]
    ]
    if dirty:
        raise MainlineError(
            "current worktree is dirty: "
            + format_dirty(dirty)
        )


def require_detached_is_at_main(audit: dict[str, object]) -> None:
    current_branch_name = audit["current_branch"]
    main = audit["main"]
    assert isinstance(main, dict)
    if current_branch_name is None and audit["current_head"] != main["sha"]:
        raise MainlineError(
            "detached HEAD is not at main; preserve it on a named branch before continuing"
        )


def require_no_active_drift(audit: dict[str, object]) -> None:
    active = audit["active_newer_than_main"]
    assert isinstance(active, dict)
    branches = active["branches"]
    detached = active["detached"]
    if not branches and not detached:
        return
    lines = ["newer-than-main work still exists outside main:"]
    for branch in branches:
        lines.append(
            f"- branch {branch['name']} @ {branch['sha']} (+{branch['ahead_of_main']})"
        )
    for candidate in detached:
        lines.append(f"- detached {candidate['path']} @ {candidate['sha']}")
    raise MainlineError("\n".join(lines))


def require_main_available(audit: dict[str, object]) -> None:
    main_elsewhere = audit["main_checked_out_elsewhere"]
    if main_elsewhere:
        raise MainlineError(
            f"main is checked out at {main_elsewhere}; use a clean integration worktree or free main first"
        )


def maybe_fast_forward_main_to_remote(
    repo_root: Path, *, main_branch: str, remote_main: str
) -> tuple[int, int]:
    ahead, behind = [
        int(value)
        for value in git(
            repo_root,
            "rev-list",
            "--left-right",
            "--count",
            f"{main_branch}...{remote_main}",
        ).stdout.strip().split()
    ]
    if ahead == 0 and behind > 0:
        git(repo_root, "merge", "--ff-only", remote_main)
        ahead, behind = [
            int(value)
            for value in git(
                repo_root,
                "rev-list",
                "--left-right",
                "--count",
                f"{main_branch}...{remote_main}",
            ).stdout.strip().split()
        ]
    return ahead, behind


def run_mainline_verify(repo_root: Path) -> None:
    run(
        ["bash", "./scripts/codex_wsl_tasks.sh", "mainline-verify"],
        cwd=repo_root,
        check=True,
    )


def switch_to_main(repo_root: Path, *, main_branch: str) -> None:
    current = current_branch(repo_root)
    if current == main_branch:
        return
    git(repo_root, "switch", main_branch)


def command_branch_gate(args: argparse.Namespace) -> int:
    repo_root = repo_root_from(Path.cwd())
    dirty = dirty_entries_for(repo_root, allowed_untracked=args.allow_untracked)
    if dirty:
        print(
            "current worktree is dirty: " + format_dirty(dirty),
            file=sys.stderr,
        )
        return 1

    current_head = head_sha(repo_root)
    main_sha = git(repo_root, "rev-parse", args.main_branch).stdout.strip()
    current_ref = current_branch(repo_root)
    if current_ref is None and current_head != main_sha:
        print(
            "detached HEAD is not at main; preserve it on a named branch before continuing",
            file=sys.stderr,
        )
        return 1

    audit = build_audit(
        repo_root,
        main_branch=args.main_branch,
        remote_main=args.remote_main,
        allowed_untracked=args.allow_untracked,
    )
    try:
        require_no_active_drift(audit)
    except MainlineError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("branch-gate: clean baseline, detached/main state acceptable, no newer-than-main drift")
    return 0


def command_mainline_audit(args: argparse.Namespace) -> int:
    repo_root = repo_root_from(Path.cwd())
    audit = build_audit(
        repo_root,
        main_branch=args.main_branch,
        remote_main=args.remote_main,
        allowed_untracked=args.allow_untracked,
    )
    if args.json:
        print(json.dumps(audit, indent=2, sort_keys=True))
    else:
        print_audit(audit)
    return 0


def select_sweep_branches(
    repo_root: Path,
    audit: dict[str, object],
    explicit_branches: list[str],
) -> list[str]:
    if explicit_branches:
        return explicit_branches
    active = audit["active_newer_than_main"]
    assert isinstance(active, dict)
    return [
        str(branch["name"])
        for branch in active["branches"]
        if bool(branch["active"])
    ]


def command_mainline_sweep(args: argparse.Namespace) -> int:
    repo_root = repo_root_from(Path.cwd())
    git(repo_root, "fetch", "origin", "--prune")
    audit = build_audit(
        repo_root,
        main_branch=args.main_branch,
        remote_main=args.remote_main,
        allowed_untracked=args.allow_untracked,
    )
    try:
        require_clean_current_worktree(audit)
        require_detached_is_at_main(audit)
        require_main_available(audit)
    except MainlineError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    branches = select_sweep_branches(repo_root, audit, args.branches)
    if not branches:
        print("mainline-sweep: no newer-than-main tracked branches to fold")
        return 0

    switch_to_main(repo_root, main_branch=args.main_branch)
    maybe_fast_forward_main_to_remote(
        repo_root,
        main_branch=args.main_branch,
        remote_main=args.remote_main,
    )

    merged: list[str] = []
    for branch in branches:
        if not ref_exists(repo_root, branch):
            print(f"missing branch: {branch}", file=sys.stderr)
            return 1
        if is_ancestor(repo_root, branch, args.main_branch):
            continue
        git(repo_root, "merge", "--no-ff", "--no-edit", branch)
        merged.append(f"{branch} -> {head_sha(repo_root)}")

    if args.verify and merged:
        run_mainline_verify(repo_root)

    if not merged:
        print("mainline-sweep: selected branches were already reachable from main")
        return 0

    print("mainline-sweep merged:")
    for line in merged:
        print(f"- {line}")
    return 0


def command_origin_reconcile(args: argparse.Namespace) -> int:
    repo_root = repo_root_from(Path.cwd())
    git(repo_root, "fetch", "origin", "--prune")
    audit = build_audit(
        repo_root,
        main_branch=args.main_branch,
        remote_main=args.remote_main,
        allowed_untracked=args.allow_untracked,
    )
    try:
        require_clean_current_worktree(audit)
        require_detached_is_at_main(audit)
        require_main_available(audit)
        require_no_active_drift(audit)
    except MainlineError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    switch_to_main(repo_root, main_branch=args.main_branch)
    ahead, behind = maybe_fast_forward_main_to_remote(
        repo_root,
        main_branch=args.main_branch,
        remote_main=args.remote_main,
    )
    if ahead > 0 and behind > 0:
        print(
            "origin-reconcile: main diverged from origin/main; stop and rebuild from latest origin/main",
            file=sys.stderr,
        )
        return 1

    if ahead == 0 and behind == 0:
        print("origin-reconcile: local main already matches origin/main and no active drift remains")
        return 0

    run_mainline_verify(repo_root)
    git(repo_root, "push", "origin", f"{args.main_branch}:{args.main_branch}")
    git(repo_root, "fetch", "origin", "--prune")

    if not is_ancestor(repo_root, args.main_branch, args.remote_main):
        print(
            "origin-reconcile: pushed main is not reachable from origin/main after fetch verification",
            file=sys.stderr,
        )
        return 1

    print(
        f"origin-reconcile: pushed {args.main_branch} to {args.remote_main} and verified reachability"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit and reconcile PODPusher worktrees back to origin/main."
    )
    parser.set_defaults(allow_untracked=list(DEFAULT_ALLOWED_UNTRACKED))
    parser.add_argument(
        "--main-branch",
        default="main",
        help="Local branch used as the integration branch.",
    )
    parser.add_argument(
        "--remote-main",
        default="origin/main",
        help="Remote source-of-truth ref.",
    )
    parser.add_argument(
        "--allow-untracked",
        action="append",
        default=None,
        help="Untracked path prefix allowed in a clean-tree check.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    branch_gate = subparsers.add_parser("branch-gate", help="Fail closed on dirty or drifted baselines.")
    branch_gate.set_defaults(func=command_branch_gate)

    audit = subparsers.add_parser("mainline-audit", help="Report worktree and branch drift relative to main.")
    audit.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    audit.set_defaults(func=command_mainline_audit)

    sweep = subparsers.add_parser("mainline-sweep", help="Fold newer tracked branches into local main.")
    sweep.add_argument(
        "--verify",
        action="store_true",
        help="Run mainline-verify after merging selected branches.",
    )
    sweep.add_argument("branches", nargs="*", help="Explicit branches to merge. Defaults to top-level active drift.")
    sweep.set_defaults(func=command_mainline_sweep)

    reconcile = subparsers.add_parser(
        "origin-reconcile",
        help="Verify local main and fast-forward push it to origin/main when eligible.",
    )
    reconcile.set_defaults(func=command_origin_reconcile)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.allow_untracked is None:
        args.allow_untracked = list(DEFAULT_ALLOWED_UNTRACKED)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
