from fastapi.testclient import TestClient

from auralink.api.main import create_app
from tests.fixtures.loader import load_fixture


def test_rollup_clean_fixture_runs_end_to_end_with_single_phase(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    session = load_fixture("rollup", variant="clean")
    post = client.post("/sessions?sync=true", json=session.model_dump(mode="json"))
    assert post.status_code == 201
    session_id = post.json()["session_id"]

    report = client.get(f"/sessions/{session_id}/report")
    assert report.status_code == 200
    body = report.json()

    assert body["quality_report"]["passed"] is True
    assert body["lift_result"] is not None
    assert body["skeleton_result"] is not None

    assert body["phase_boundaries"] is not None
    assert len(body["phase_boundaries"]["phases"]) == 1
    assert body["phase_boundaries"]["phases"][0]["label"] == "full_movement"

    assert body["rep_boundaries"] is None
    assert body["per_rep_metrics"] is None
    assert body["within_movement_trend"] is None
