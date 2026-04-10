from fastapi.testclient import TestClient

from auralink.api.main import create_app

from tests.fixtures.synthetic_overhead_squat import build_overhead_squat_payload


def test_post_sessions_runs_pipeline_and_persists_artifacts(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    payload = build_overhead_squat_payload(rep_count=2, frames_per_rep=30)
    response = client.post("/sessions?sync=true", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert "session_id" in body

    session_id = body["session_id"]
    artifacts_path = tmp_path / "sessions" / f"{session_id}.artifacts.json"
    assert artifacts_path.exists(), "pipeline artifacts should be persisted after POST"


def test_sync_flag_is_accepted_as_noop(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    payload = build_overhead_squat_payload()
    r1 = client.post("/sessions?sync=true", json=payload)
    r2 = client.post("/sessions", json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 201
