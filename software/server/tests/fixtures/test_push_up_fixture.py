import json
from pathlib import Path

from bioliminal.api.schemas import Session

FIXTURE_DIR = Path(__file__).parent / "synthetic"


def test_push_up_clean_fixture_loads_as_session():
    path = FIXTURE_DIR / "push_up_clean.json"
    assert path.exists(), f"missing fixture: {path}"
    session = Session.model_validate(json.loads(path.read_text()))
    assert session.metadata.movement == "push_up"
    assert len(session.frames) == 60
