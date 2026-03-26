from pathlib import Path


SCRIPT_PATH = Path("scripts/codex_wsl_tasks.sh")


def test_mainline_verify_keeps_the_fail_closed_validation_ladder() -> None:
    content = SCRIPT_PATH.read_text(encoding="utf-8")

    required_steps = [
        '"$CODEX_WSL_VENV_DIR/bin/python" -m flake8',
        '"$CODEX_WSL_VENV_DIR/bin/python" scripts/verify_translations.py',
        '"$CODEX_WSL_VENV_DIR/bin/python" -m alembic upgrade head',
        '"$CODEX_WSL_VENV_DIR/bin/python" -m pytest tests -q -s',
        "npm exec --prefix client tsc -- --noEmit --project client/tsconfig.json",
        "npm test --prefix client -- --runInBand",
        "npm run build --prefix client",
        "npm exec --prefix client playwright -- test",
    ]

    positions = [content.index(step) for step in required_steps]
    assert positions == sorted(positions)
