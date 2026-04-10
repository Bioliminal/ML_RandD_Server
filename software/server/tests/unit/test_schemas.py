import pytest
from pydantic import ValidationError

from auralink.api.schemas import Landmark, Frame


def test_landmark_valid():
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=0.95, presence=0.99)
    assert lm.x == 0.5
    assert lm.visibility == 0.95


def test_landmark_rejects_out_of_range_visibility():
    with pytest.raises(ValidationError):
        Landmark(x=0.5, y=0.5, z=0.0, visibility=1.5, presence=0.99)


def test_frame_requires_33_landmarks():
    landmarks = [
        Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0, presence=1.0)
        for _ in range(33)
    ]
    frame = Frame(timestamp_ms=0, landmarks=landmarks)
    assert len(frame.landmarks) == 33


def test_frame_rejects_wrong_landmark_count():
    landmarks = [
        Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0, presence=1.0)
        for _ in range(10)
    ]
    with pytest.raises(ValidationError):
        Frame(timestamp_ms=0, landmarks=landmarks)
