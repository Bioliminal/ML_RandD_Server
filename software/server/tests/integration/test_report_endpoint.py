from fastapi.testclient import TestClient

from auralink.api.main import create_app

from tests.fixtures.synthetic_overhead_squat import build_overhead_squat_payload


def test_get_report_returns_artifacts_after_post(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    post = client.post("/sessions?sync=true", json=build_overhead_squat_payload())
    session_id = post.json()["session_id"]

    response = client.get(f"/sessions/{session_id}/report")
    assert response.status_code == 200
    body = response.json()
    assert body["quality_report"]["passed"] is True
    assert body["angle_series"] is not None
    assert body["within_movement_trend"] is not None


def test_get_report_404_when_session_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    response = client.get("/sessions/does-not-exist/report")
    assert response.status_code == 404
