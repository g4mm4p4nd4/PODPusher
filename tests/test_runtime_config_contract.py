from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPOSE_PATH = ROOT / "docker-compose.yml"
ENV_EXAMPLE_PATH = ROOT / ".env.example"
DOCKERFILE_PATH = ROOT / "Dockerfile"
PROMETHEUS_PATH = ROOT / "prometheus" / "prometheus.yml"
GRAFANA_DATASOURCE_PATH = ROOT / "grafana" / "provisioning" / "datasources" / "prometheus.yml"


def _compose_content() -> str:
    return COMPOSE_PATH.read_text(encoding="utf-8")


def test_integration_service_uses_oauth_env_contract() -> None:
    content = _compose_content()

    required = {
        "PRINTIFY_CLIENT_ID: ${PRINTIFY_CLIENT_ID:-}",
        "PRINTIFY_CLIENT_SECRET: ${PRINTIFY_CLIENT_SECRET:-}",
        "ETSY_CLIENT_ID: ${ETSY_CLIENT_ID:-}",
        "ETSY_CLIENT_SECRET: ${ETSY_CLIENT_SECRET:-}",
    }
    for expected in required:
        assert expected in content

    assert "ETSY_API_KEY=${ETSY_API_KEY}" not in content


def test_local_compose_has_trend_observability_stack() -> None:
    content = _compose_content()

    for service in (
        "  gateway:",
        "  trend_ingestion:",
        "  worker:",
        "  frontend:",
        "  prometheus:",
        "  grafana:",
        "  ollama:",
        "  ollama-pull:",
        "  db:",
        "  redis:",
    ):
        assert service in content

    assert "dockerfile: Dockerfile" in content
    assert "TREND_INGESTION_STUB: ${TREND_INGESTION_STUB:-0}" in content
    assert "DATABASE_URL: ${DATABASE_URL:-postgresql+psycopg://user:pass@db:5432/pod}" in content


def test_env_example_documents_no_key_trend_defaults() -> None:
    content = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

    assert "DATABASE_URL=postgresql+psycopg://user:pass@db:5432/pod" in content
    assert "TREND_INGESTION_STUB=0" in content
    assert "TREND_INGESTION_SCRAPEGRAPH=1" in content
    assert "SCRAPEGRAPH_MODEL=ollama/llama3.2" in content
    assert "OLLAMA_BASE_URL=http://ollama:11434" in content


def test_dockerfile_installs_playwright_and_scrapegraphai_dependency() -> None:
    dockerfile = DOCKERFILE_PATH.read_text(encoding="utf-8")
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")

    assert "python -m playwright install --with-deps chromium" in dockerfile
    assert "scrapegraphai" in requirements


def test_prometheus_and_grafana_are_wired_for_local_metrics() -> None:
    prometheus = PROMETHEUS_PATH.read_text(encoding="utf-8")
    datasource = GRAFANA_DATASOURCE_PATH.read_text(encoding="utf-8")

    assert "gateway:8000" in prometheus
    assert "trend_ingestion:8007" in prometheus
    assert "/etc/prometheus/alerts/*.yml" in prometheus
    assert "url: http://prometheus:9090" in datasource
