from fastapi.testclient import TestClient

from auralink.api.main import create_app

from tests.fixtures.synthetic_overhead_squat import build_overhead_squat_payload


def test_overhead_squat_round_trip_produces_populated_report(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    payload = build_overhead_squat_payload(rep_count=3, frames_per_rep=30)
    post = client.post("/sessions?sync=true", json=payload)
    assert post.status_code == 201
    session_id = post.json()["session_id"]

    report = client.get(f"/sessions/{session_id}/report")
    assert report.status_code == 200
    body = report.json()

    assert body["quality_report"]["passed"] is True
    assert body["angle_series"]["angles"]["left_knee_flexion"]
    assert body["normalized_angle_series"]["scale_factor"] > 0
    assert len(body["rep_boundaries"]["by_angle"]["left_knee_flexion"]) == 3
    assert len(body["per_rep_metrics"]["reps"]) == 3
    assert "fatigue_detected" in body["within_movement_trend"]
