from fastapi.testclient import TestClient

from auralink.api.main import create_app
from tests.fixtures.loader import load_fixture


def test_single_leg_squat_clean_fixture_runs_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    session = load_fixture("single_leg_squat", variant="clean")
    post = client.post("/sessions?sync=true", json=session.model_dump(mode="json"))
    assert post.status_code == 201
    session_id = post.json()["session_id"]

    report = client.get(f"/sessions/{session_id}/report")
    assert report.status_code == 200
    body = report.json()

    section = body["movement_section"]
    assert section["quality_report"]["passed"] is True
    assert section["lift_result"] is not None
    assert section["skeleton_result"] is not None
    assert section["per_rep_metrics"] is not None
    assert section["phase_boundaries"] is None
