from fastapi.testclient import TestClient

from bioliminal.api.main import create_app
from tests.fixtures.loader import load_fixture


def _post_session(client: TestClient, movement: str, variant: str = "clean") -> str:
    session = load_fixture(movement, variant=variant)
    post = client.post("/sessions", json=session.model_dump(mode="json"))
    assert post.status_code in (200, 201)
    return post.json()["session_id"]


def test_protocol_with_single_session_returns_report(tmp_path, monkeypatch):
    monkeypatch.setenv("BIOLIMINAL_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    sid = _post_session(client, "overhead_squat", "clean")

    resp = client.post("/protocols", json={"session_ids": [sid]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_ids"] == [sid]
    assert body["per_session_movements"][sid] == "overhead_squat"
    assert body["fatigue_carryover_detected"] is False


def test_protocol_missing_session_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("BIOLIMINAL_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    resp = client.post("/protocols", json={"session_ids": ["00000000-0000-0000-0000-000000000000"]})
    assert resp.status_code == 404


def test_protocol_empty_session_list_returns_422(tmp_path, monkeypatch):
    monkeypatch.setenv("BIOLIMINAL_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    resp = client.post("/protocols", json={"session_ids": []})
    assert resp.status_code == 422


def test_protocol_two_sessions_produces_cross_movement_metrics(tmp_path, monkeypatch):
    monkeypatch.setenv("BIOLIMINAL_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    sid_a = _post_session(client, "overhead_squat", "clean")
    sid_b = _post_session(client, "single_leg_squat", "clean")

    resp = client.post("/protocols", json={"session_ids": [sid_a, sid_b]})
    assert resp.status_code == 200
    body = resp.json()
    metric_names = {m["metric_name"] for m in body["cross_movement_metrics"]}
    assert "mean_ncc" in metric_names
    assert body["fatigue_carryover_detected"] is False
