from pathlib import Path


CODEX_WSL_DOC = Path("docs/codex-wsl.md")
AUTOMATION_CONTROL_DOC = Path("docs/automation_control_plane.md")
SOURCE_OF_TRUTH_DOC = Path("docs/source_of_truth_integration.md")
STATUS_DOC = Path("status.md")


def test_docs_align_on_repo_owned_convergence_commands() -> None:
    codex_wsl = CODEX_WSL_DOC.read_text(encoding="utf-8")
    source = SOURCE_OF_TRUTH_DOC.read_text(encoding="utf-8")

    assert "./scripts/codex_wsl_tasks.sh branch-gate" in codex_wsl
    assert "./scripts/codex_wsl_tasks.sh mainline-sweep --verify" in codex_wsl
    assert "./scripts/codex_wsl_tasks.sh origin-reconcile" in codex_wsl

    assert "./scripts/codex_wsl_tasks.sh mainline-audit" in source
    assert "./scripts/codex_wsl_tasks.sh mainline-sweep --verify" in source
    assert "./scripts/codex_wsl_tasks.sh origin-reconcile" in source


def test_status_requires_explicit_terminal_mainline_disposition() -> None:
    status = STATUS_DOC.read_text(encoding="utf-8")

    assert "State: `ACTIVE`" in status
    assert "merged into local `main` via `mainline-sweep`" in status
    assert "preserved on a named tracked branch with branch name and `HEAD` SHA reported" in status
    assert "blocked with branch name or detached `HEAD` SHA plus a concrete reason" in status
    assert "`origin-reconcile` may only no-op" in status


def test_automation_control_doc_captures_live_state_contract() -> None:
    content = AUTOMATION_CONTROL_DOC.read_text(encoding="utf-8")

    assert "ACTIVE" in content
    assert "mainline-audit --json" in content
    assert "structured stop record" in content
    assert "no active newer-than-main drift" in content
    assert "mainline-sweep --verify" in content
    assert "origin-reconcile" in content
