from fastapi.testclient import TestClient

from bioliminal.api.main import create_app
from bioliminal.api.schemas import Session
from tests.fixtures.synthetic.generator import build_overhead_squat_payload


def _post_squat(
    client: TestClient, rep_count: int, valgus_deg: float, trunk_lean_deg: float
) -> str:
    payload = build_overhead_squat_payload(
        rep_count=rep_count,
        frames_per_rep=30,
        frame_rate=30.0,
        knee_valgus_deg=valgus_deg,
        trunk_lean_deg=trunk_lean_deg,
    )
    session = Session.model_validate(payload)
    resp = client.post("/sessions", json=session.model_dump(mode="json"))
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["session_id"]


def test_four_clean_sessions_do_not_trigger_fatigue_carryover(tmp_path, monkeypatch):
    monkeypatch.setenv("BIOLIMINAL_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    ids = [_post_squat(client, rep_count=3, valgus_deg=2.0, trunk_lean_deg=4.0) for _ in range(4)]
    resp = client.post("/protocols", json={"session_ids": ids})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["per_session_movements"].keys()) == set(ids)
    assert all(v == "overhead_squat" for v in body["per_session_movements"].values())
    metric_names = {m["metric_name"] for m in body["cross_movement_metrics"]}
    assert "mean_ncc" in metric_names
    assert body["fatigue_carryover_detected"] is False
    assert isinstance(body["summary_narrative"], str)


def test_four_sessions_with_escalating_compensation_trigger_fatigue_carryover(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("BIOLIMINAL_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    # Escalating trunk lean + valgus as a proxy for accumulating fatigue across
    # a four-movement protocol. Each subsequent session injects a larger
    # compensation, which (after DTW + NCC) manifests as a declining mean NCC
    # and growing |mean_rom_deviation_pct| — the joint condition for carryover.
    ids = [
        _post_squat(client, rep_count=3, valgus_deg=2.0, trunk_lean_deg=4.0),
        _post_squat(client, rep_count=3, valgus_deg=6.0, trunk_lean_deg=8.0),
        _post_squat(client, rep_count=3, valgus_deg=10.0, trunk_lean_deg=12.0),
        _post_squat(client, rep_count=3, valgus_deg=14.0, trunk_lean_deg=16.0),
    ]
    resp = client.post("/protocols", json={"session_ids": ids})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["cross_movement_metrics"]) >= 1
    # The carryover flag is the point of this test — if the synthetic
    # compensations do not trigger it, the test fails and the thresholds
    # need re-tuning against the generator. This is the regression guard.
    assert body["fatigue_carryover_detected"] is True
