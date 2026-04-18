from fastapi.testclient import TestClient

from bioliminal.api.main import create_app
from tests.fixtures.synthetic.generator import build_overhead_squat_payload


def test_overhead_squat_round_trip_produces_populated_report(tmp_path, monkeypatch):
    monkeypatch.setenv("BIOLIMINAL_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    payload = build_overhead_squat_payload(rep_count=3, frames_per_rep=30)
    post = client.post("/sessions?sync=true", json=payload)
    assert post.status_code == 201
    session_id = post.json()["session_id"]

    report = client.get(f"/sessions/{session_id}/report")
    assert report.status_code == 200
    body = report.json()

    section = body["movement_section"]
    assert section["quality_report"]["passed"] is True
    assert section["angle_series"]["angles"]["left_knee_flexion"]
    assert section["normalized_angle_series"]["scale_factor"] > 0
    assert len(section["rep_boundaries"]["by_angle"]["left_knee_flexion"]) == 3
    assert len(section["per_rep_metrics"]["reps"]) == 3
    assert "fatigue_detected" in section["within_movement_trend"]
