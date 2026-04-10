from fastapi.testclient import TestClient

from auralink.api.main import create_app


def _sample_payload() -> dict:
    landmark = {
        "x": 0.5,
        "y": 0.5,
        "z": 0.0,
        "visibility": 1.0,
        "presence": 1.0,
    }
    frame = {
        "timestamp_ms": 0,
        "landmarks": [landmark for _ in range(33)],
    }
    return {
        "metadata": {
            "movement": "overhead_squat",
            "device": "Pixel 8",
            "model": "mlkit_pose_detection",
            "frame_rate": 30.0,
        },
        "frames": [frame],
    }


def test_post_session_returns_id(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    response = client.post("/sessions", json=_sample_payload())
    assert response.status_code == 201
    body = response.json()
    assert "session_id" in body
    assert body["frames_received"] == 1


def test_post_session_rejects_bad_landmark_count(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    payload = _sample_payload()
    payload["frames"][0]["landmarks"] = payload["frames"][0]["landmarks"][:10]
    response = client.post("/sessions", json=payload)
    assert response.status_code == 422


def test_get_session_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    post_response = client.post("/sessions", json=_sample_payload())
    session_id = post_response.json()["session_id"]

    get_response = client.get(f"/sessions/{session_id}")
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["metadata"]["movement"] == "overhead_squat"
    assert len(body["frames"]) == 1
