import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path("scripts/apply_codex_wsl_migration.py")


def load_migration_module():
    spec = importlib.util.spec_from_file_location("apply_codex_wsl_migration", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_origin_reconcile_prompt_calls_repo_owned_command() -> None:
    module = load_migration_module()

    assert "./scripts/codex_wsl_tasks.sh origin-reconcile" in module.ORIGIN_RECONCILE_PROMPT
    assert "refuses a no-op exit" in module.ORIGIN_RECONCILE_PROMPT
    assert "./scripts/codex_wsl_tasks.sh mainline-verify" in module.ORIGIN_RECONCILE_PROMPT
    assert "fast-forward pushes local main to origin/main" in module.ORIGIN_RECONCILE_PROMPT


def test_mainline_sweep_prompt_calls_repo_owned_command() -> None:
    module = load_migration_module()

    assert "./scripts/codex_wsl_tasks.sh mainline-sweep --verify" in module.MAINLINE_SWEEP_PROMPT
    assert "newer-than-main tracked branches" in module.MAINLINE_SWEEP_PROMPT
    assert "git merge --no-ff" in module.MAINLINE_SWEEP_PROMPT
    assert "Do not push to origin" in module.MAINLINE_SWEEP_PROMPT
