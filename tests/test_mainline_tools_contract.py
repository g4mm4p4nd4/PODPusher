import importlib.util
import sys
from pathlib import Path


SHELL_SCRIPT = Path("scripts/codex_wsl_tasks.sh")
TOOLS_SCRIPT = Path("scripts/mainline_tools.py")


def load_mainline_tools():
    spec = importlib.util.spec_from_file_location("mainline_tools", TOOLS_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_shell_entrypoints_expose_mainline_commands() -> None:
    content = SHELL_SCRIPT.read_text(encoding="utf-8")

    assert "branch-gate" in content
    assert "mainline-audit" in content
    assert "mainline-sweep" in content
    assert "origin-reconcile" in content
    assert 'python3 "$CODEX_WSL_REPO_ROOT/scripts/mainline_tools.py"' in content


def test_mainline_tools_parser_exposes_expected_subcommands() -> None:
    module = load_mainline_tools()
    parser = module.build_parser()
    help_text = parser.format_help()

    assert "branch-gate" in help_text
    assert "mainline-audit" in help_text
    assert "mainline-sweep" in help_text
    assert "origin-reconcile" in help_text


def test_mainline_tools_allow_automation_scratch_paths() -> None:
    module = load_mainline_tools()

    assert "automation/" in module.DEFAULT_ALLOWED_UNTRACKED
    assert "scripts/automation/" in module.DEFAULT_ALLOWED_UNTRACKED


def test_default_sweep_selection_only_uses_active_branches() -> None:
    module = load_mainline_tools()
    audit = {
        "active_newer_than_main": {
            "branches": [
                {"name": "codex/frontend/recreate-pr70", "active": True},
                {"name": "pr/84", "active": False},
            ]
        }
    }

    selected = module.select_sweep_branches(Path("."), audit, [])
    assert selected == ["codex/frontend/recreate-pr70"]
