from fastapi.testclient import TestClient

from bioliminal.api.main import create_app


def test_health_endpoint():
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "bioliminal-server"


def test_health_publishes_default_retention_days():
    """ML#20: smoke / mobile / privacy auditors can read the active retention
    window without a separate /privacy endpoint."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["default_retention_days"] == 30
