import json
from pathlib import Path

from bioliminal.api.schemas import Session

FIXTURE_DIR = Path(__file__).parent / "synthetic"


def _load(name: str) -> Session:
    path = FIXTURE_DIR / name
    assert path.exists(), f"missing fixture: {path}"
    return Session.model_validate(json.loads(path.read_text()))


def test_overhead_squat_clean_fixture_loads_as_session():
    session = _load("overhead_squat_clean.json")
    assert session.metadata.movement == "overhead_squat"
    assert len(session.frames) == 60


def test_overhead_squat_valgus_fixture_loads_as_session():
    session = _load("overhead_squat_valgus.json")
    assert session.metadata.movement == "overhead_squat"
    assert len(session.frames) == 60
