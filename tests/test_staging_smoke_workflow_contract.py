from pathlib import Path


WORKFLOW_PATH = Path(".github/workflows/staging-smoke.yml")


def test_staging_smoke_workflow_has_secret_preflight_and_artifact_upload():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "Validate required staging secrets" in content
    assert "Missing required staging secrets:" in content
    assert "--junitxml=staging-smoke-junit.xml" in content
    assert "uses: actions/upload-artifact@v4" in content
    assert "name: staging-smoke-junit" in content
