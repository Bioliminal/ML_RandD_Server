import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from auralink.temporal.reference_reps import ReferenceRep, load_reference_rep


def _write_ref(tmp_path: Path, movement: str, payload: dict) -> Path:
    p = tmp_path / f"{movement}.json"
    p.write_text(json.dumps(payload))
    return p


def test_load_valid_reference_rep(tmp_path):
    _write_ref(
        tmp_path,
        "overhead_squat",
        {
            "movement": "overhead_squat",
            "angles": {
                "left_knee_flexion": [90.0, 100.0, 110.0, 120.0, 130.0],
                "trunk_lean": [4.0, 4.0, 4.0, 4.0, 4.0],
            },
            "frame_rate": 30.0,
            "frames_per_rep": 5,
        },
    )
    rep = load_reference_rep("overhead_squat", config_dir=tmp_path)
    assert isinstance(rep, ReferenceRep)
    assert rep.movement == "overhead_squat"
    assert rep.frames_per_rep == 5
    assert rep.angles["left_knee_flexion"][0] == 90.0


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_reference_rep("overhead_squat", config_dir=tmp_path)


def test_invalid_schema_raises(tmp_path):
    _write_ref(
        tmp_path,
        "overhead_squat",
        {
            "movement": "overhead_squat",
            "angles": {},
            "frame_rate": 30.0,
            "frames_per_rep": 5,
        },
    )
    with pytest.raises(ValidationError):
        load_reference_rep("overhead_squat", config_dir=tmp_path)


def test_angle_keys_returns_set(tmp_path):
    _write_ref(
        tmp_path,
        "push_up",
        {
            "movement": "push_up",
            "angles": {
                "left_elbow_flexion": [90.0, 100.0, 110.0],
                "right_elbow_flexion": [90.0, 100.0, 110.0],
            },
            "frame_rate": 30.0,
            "frames_per_rep": 3,
        },
    )
    rep = load_reference_rep("push_up", config_dir=tmp_path)
    assert rep.angle_keys() == {"left_elbow_flexion", "right_elbow_flexion"}
