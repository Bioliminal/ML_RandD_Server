import copy

from fastapi.testclient import TestClient

from auralink.api.main import create_app

from tests.fixtures.synthetic_overhead_squat import build_overhead_squat_payload


def test_quality_gate_rejection_returns_422(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    payload = copy.deepcopy(build_overhead_squat_payload())
    payload["metadata"]["frame_rate"] = 10.0  # below MIN_FRAME_RATE = 20

    response = client.post("/sessions?sync=true", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "quality_gate_rejected"
    assert any(issue["code"] == "low_frame_rate" for issue in body["issues"])


from unittest.mock import patch

from auralink.pipeline.errors import StageError


def test_stage_error_returns_500_with_stage_detail(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    payload = build_overhead_squat_payload()

    def _boom(session, registry=None):
        raise StageError(stage_name="angle_series", detail="simulated failure")

    with patch("auralink.api.routes.sessions.run_pipeline", _boom):
        response = client.post("/sessions?sync=true", json=payload)

    assert response.status_code == 500
    body = response.json()
    assert body["error"] == "stage_failed"
    assert body["stage"] == "angle_series"
    assert body["detail"] == "simulated failure"


from auralink.pipeline.errors import PipelineError


def test_generic_pipeline_error_returns_500(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    payload = build_overhead_squat_payload()

    def _boom(session, registry=None):
        raise PipelineError("no stages registered for movement 'mystery'")

    with patch("auralink.api.routes.sessions.run_pipeline", _boom):
        response = client.post("/sessions?sync=true", json=payload)

    assert response.status_code == 500
    body = response.json()
    assert body["error"] == "pipeline_failed"
    assert "mystery" in body["detail"]
