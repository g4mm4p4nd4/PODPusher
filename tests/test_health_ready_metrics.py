from fastapi.testclient import TestClient
from services.gateway.api import app

def test_health_ready_endpoints():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ok"}


def test_metrics_increment():
    client = TestClient(app)
    client.get("/health")
    metrics = client.get("/metrics").text
    assert "http_requests_total" in metrics
