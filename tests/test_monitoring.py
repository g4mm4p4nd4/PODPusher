import json
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.common.logger import init_logger, logging_middleware
from services.common.monitoring import init_monitoring


def _build_app() -> FastAPI:
    init_logger()
    app = FastAPI()
    app.middleware("http")(logging_middleware)
    init_monitoring(app)

    @app.get("/")
    async def root():
        from loguru import logger

        logger.info("hello")
        return {"ok": True}

    return app


def test_logger_includes_correlation_id():
    app = _build_app()
    client = TestClient(app)
    logs: list[str] = []

    from loguru import logger

    logger.add(lambda msg: logs.append(msg), serialize=True)

    response = client.get("/", headers={"X-Correlation-ID": "abc123"})
    assert response.headers["X-Correlation-ID"] == "abc123"
    data = json.loads(logs[0])
    assert data["record"]["extra"]["correlation_id"] == "abc123"


def test_health_ready_metrics_endpoints():
    app = _build_app()
    client = TestClient(app)

    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
    # trigger a request so metrics have data
    client.get("/health")
    metrics_resp = client.get("/metrics")
    assert metrics_resp.status_code == 200
    assert "http_requests_total" in metrics_resp.text
