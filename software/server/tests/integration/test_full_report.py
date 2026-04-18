from fastapi.testclient import TestClient

from bioliminal.api.main import create_app
from tests.fixtures.loader import load_fixture


def test_overhead_squat_valgus_produces_sbl_observation(tmp_path, monkeypatch):
    monkeypatch.setenv("BIOLIMINAL_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    session = load_fixture("overhead_squat", variant="valgus")
    post = client.post("/sessions", json=session.model_dump(mode="json"))
    assert post.status_code in (200, 201)
    session_id = post.json()["session_id"]

    report = client.get(f"/sessions/{session_id}/report")
    assert report.status_code == 200
    body = report.json()
    observations = body["movement_section"]["chain_observations"]
    sbl_obs = [
        o
        for o in observations
        if o["chain"] == "superficial_back_line" and o["severity"] in {"concern", "flag"}
    ]
    assert (
        len(sbl_obs) >= 1
    ), f"expected at least one SBL concern/flag observation, got {observations}"


def test_overhead_squat_clean_produces_no_observations(tmp_path, monkeypatch):
    monkeypatch.setenv("BIOLIMINAL_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    session = load_fixture("overhead_squat", variant="clean")
    post = client.post("/sessions", json=session.model_dump(mode="json"))
    assert post.status_code in (200, 201)
    session_id = post.json()["session_id"]

    report = client.get(f"/sessions/{session_id}/report")
    assert report.status_code == 200
    body = report.json()
    assert body["movement_section"]["chain_observations"] == []
    assert "clean overall pattern" in body["overall_narrative"]


def test_single_leg_squat_clean_runs_end_to_end_with_bfl_rule_loaded(tmp_path, monkeypatch):
    """BFL rule coverage — single_leg_squat is the movement the BFL rule applies to.

    Note: the synthetic `single_leg_squat_clean` fixture does not inject a
    compensation, so it may or may not produce an observation depending on
    baseline pose values. The assertion is structural: a successful e2e run
    with BFL rules loaded, no 5xx, and either 0 observations or any
    observation that (if present) belongs to a recognized chain.
    """
    monkeypatch.setenv("BIOLIMINAL_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    session = load_fixture("single_leg_squat", variant="clean")
    post = client.post("/sessions", json=session.model_dump(mode="json"))
    assert post.status_code in (200, 201)
    session_id = post.json()["session_id"]

    report = client.get(f"/sessions/{session_id}/report")
    assert report.status_code == 200
    body = report.json()
    assert body["movement_section"]["movement"] == "single_leg_squat"
    recognized_chains = {
        "superficial_back_line",
        "back_functional_line",
        "front_functional_line",
    }
    for obs in body["movement_section"]["chain_observations"]:
        assert obs["chain"] in recognized_chains
