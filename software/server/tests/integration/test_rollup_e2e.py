from fastapi.testclient import TestClient

from bioliminal.api.main import create_app
from tests.fixtures.loader import load_fixture


def test_rollup_clean_fixture_runs_end_to_end_with_single_phase(tmp_path, monkeypatch):
    monkeypatch.setenv("BIOLIMINAL_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    session = load_fixture("rollup", variant="clean")
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

    assert section["phase_boundaries"] is not None
    assert len(section["phase_boundaries"]["phases"]) == 1
    assert section["phase_boundaries"]["phases"][0]["label"] == "full_movement"

    assert section["rep_boundaries"] is None
    assert section["per_rep_metrics"] is None
    assert section["within_movement_trend"] is None
