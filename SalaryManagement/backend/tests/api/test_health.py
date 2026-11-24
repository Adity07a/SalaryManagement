from app.main import app
from fastapi.testclient import TestClient


def test_health_endpoint_reports_process_liveness() -> None:
    """Liveness remains available independently of database connectivity."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
