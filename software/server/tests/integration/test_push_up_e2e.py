from fastapi.testclient import TestClient

from auralink.api.main import create_app
from tests.fixtures.loader import load_fixture


def test_push_up_clean_fixture_runs_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    session = load_fixture("push_up", variant="clean")
    post = client.post("/sessions?sync=true", json=session.model_dump(mode="json"))
    assert post.status_code == 201
    session_id = post.json()["session_id"]

    report = client.get(f"/sessions/{session_id}/report")
    assert report.status_code == 200
    body = report.json()

    assert body["quality_report"]["passed"] is True
    assert body["lift_result"] is not None
    assert body["skeleton_result"] is not None
    # push_up pipeline stops at skeleton — rep-based stages require
    # elbow_flexion (deferred). See Task 9 and the stage composition matrix.
    assert body["rep_boundaries"] is None
    assert body["per_rep_metrics"] is None
    assert body["within_movement_trend"] is None
    assert body["phase_boundaries"] is None
