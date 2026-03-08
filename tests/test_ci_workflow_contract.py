from pathlib import Path


WORKFLOW_PATH = Path('.github/workflows/ci.yml')


def test_ci_workflow_enforces_frontend_quality_gates() -> None:
    content = WORKFLOW_PATH.read_text(encoding='utf-8')

    assert "name: Frontend type-check" in content
    assert "npm exec --prefix client tsc -- --noEmit --project client/tsconfig.json" in content

    assert "name: Frontend build" in content
    assert "npm run build --prefix client" in content

    assert "name: Node tests" in content
    assert "npm test --prefix client" in content


def test_ci_workflow_keeps_migration_and_playwright_checks() -> None:
    content = WORKFLOW_PATH.read_text(encoding='utf-8')

    assert "name: Alembic upgrade check" in content
    assert "alembic upgrade head" in content

    assert "name: Playwright tests" in content
    assert "npm exec --prefix client playwright -- test" in content
