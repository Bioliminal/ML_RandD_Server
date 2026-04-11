import copy

from fastapi.testclient import TestClient

from auralink.api.main import create_app
from tests.fixtures.synthetic.generator import build_overhead_squat_payload


def test_post_session_returns_id(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    payload = build_overhead_squat_payload(rep_count=2, frames_per_rep=30)
    response = client.post("/sessions", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert "session_id" in body
    assert body["frames_received"] == 60


def test_post_session_rejects_bad_landmark_count(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    payload = copy.deepcopy(build_overhead_squat_payload(rep_count=2, frames_per_rep=30))
    payload["frames"][0]["landmarks"] = payload["frames"][0]["landmarks"][:10]
    response = client.post("/sessions", json=payload)
    assert response.status_code == 422


def test_get_session_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    payload = build_overhead_squat_payload(rep_count=2, frames_per_rep=30)
    post_response = client.post("/sessions", json=payload)
    session_id = post_response.json()["session_id"]

    get_response = client.get(f"/sessions/{session_id}")
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["metadata"]["movement"] == "overhead_squat"
    assert len(body["frames"]) == 60
