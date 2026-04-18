import json

import pytest

from bioliminal.api.schemas import Session
from tests.fixtures.loader import load_fixture
from tests.fixtures.synthetic.generator import generate_session


def _write(tmp_path, movement: str, variant: str) -> None:
    syn = tmp_path / "synthetic"
    syn.mkdir(exist_ok=True)
    payload = generate_session(movement, rep_count=1, frames_per_rep=30)
    (syn / f"{movement}_{variant}.json").write_text(json.dumps(payload))


def test_load_fixture_discovers_by_pattern(tmp_path):
    _write(tmp_path, "overhead_squat", "clean")
    session = load_fixture("overhead_squat", variant="clean", search_dir=tmp_path / "synthetic")
    assert isinstance(session, Session)
    assert session.metadata.movement == "overhead_squat"


def test_load_fixture_defaults_to_clean_variant(tmp_path):
    _write(tmp_path, "overhead_squat", "clean")
    a = load_fixture("overhead_squat", search_dir=tmp_path / "synthetic")
    b = load_fixture("overhead_squat", variant="clean", search_dir=tmp_path / "synthetic")
    assert a.metadata.movement == b.metadata.movement
    assert len(a.frames) == len(b.frames)


def test_load_fixture_unknown_variant_raises_file_not_found(tmp_path):
    (tmp_path / "synthetic").mkdir()
    with pytest.raises(FileNotFoundError):
        load_fixture("overhead_squat", variant="does_not_exist", search_dir=tmp_path / "synthetic")
