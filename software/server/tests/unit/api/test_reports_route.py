from fastapi.testclient import TestClient

from bioliminal.api.main import create_app


def test_get_report_returns_404_for_missing_session(tmp_path, monkeypatch):
    monkeypatch.setenv("BIOLIMINAL_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    response = client.get("/sessions/does-not-exist/report")
    assert response.status_code == 404
