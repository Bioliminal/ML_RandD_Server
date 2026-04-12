import json
from pathlib import Path

from auralink.api.schemas import Session

FIXTURE_DIR = Path(__file__).parent / "synthetic"


def test_rollup_clean_fixture_loads_as_session():
    path = FIXTURE_DIR / "rollup_clean.json"
    assert path.exists(), f"missing fixture: {path}"
    session = Session.model_validate(json.loads(path.read_text()))
    assert session.metadata.movement == "rollup"
    assert len(session.frames) == 60
