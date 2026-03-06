from pathlib import Path


def _integration_env_lines() -> list[str]:
    compose_path = Path(__file__).resolve().parents[1] / "docker-compose.yml"
    lines = compose_path.read_text(encoding="utf-8").splitlines()

    integration_index = lines.index("  integration:")
    env_index = lines.index("    environment:", integration_index)

    env_lines: list[str] = []
    for line in lines[env_index + 1 :]:
        if line.startswith("  ") and not line.startswith("      - "):
            break
        if line.startswith("      - "):
            env_lines.append(line.removeprefix("      - "))
    return env_lines


def test_integration_service_uses_oauth_env_contract() -> None:
    env_lines = _integration_env_lines()

    required = {
        "PRINTIFY_CLIENT_ID=${PRINTIFY_CLIENT_ID}",
        "PRINTIFY_CLIENT_SECRET=${PRINTIFY_CLIENT_SECRET}",
        "ETSY_CLIENT_ID=${ETSY_CLIENT_ID}",
        "ETSY_CLIENT_SECRET=${ETSY_CLIENT_SECRET}",
    }
    for expected in required:
        assert expected in env_lines

    assert "ETSY_API_KEY=${ETSY_API_KEY}" not in env_lines
