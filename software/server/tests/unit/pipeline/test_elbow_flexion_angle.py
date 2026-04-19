import math

import pytest

from bioliminal.api.schemas import Frame, PoseLandmark
from bioliminal.pose.joint_angles import elbow_flexion_angle


def _make_frame(landmarks_by_idx: dict[int, tuple[float, float]]) -> Frame:
    landmarks = []
    for idx in range(33):
        if idx in landmarks_by_idx:
            x, y = landmarks_by_idx[idx]
        else:
            x, y = 0.5, 0.5
        landmarks.append(
            PoseLandmark(x=x, y=y, z=0.0, visibility=1.0, presence=1.0)
        )
    return Frame(timestamp_ms=0, landmarks=landmarks)


def test_left_elbow_fully_extended_is_180_deg():
    frame = _make_frame({11: (0.0, 0.0), 13: (1.0, 0.0), 15: (2.0, 0.0)})
    assert elbow_flexion_angle(frame, "left") == pytest.approx(180.0, abs=0.1)


def test_left_elbow_fully_flexed_is_0_deg():
    frame = _make_frame({11: (0.0, 0.0), 13: (1.0, 0.0), 15: (0.0, 0.0)})
    assert elbow_flexion_angle(frame, "left") == pytest.approx(0.0, abs=0.1)


def test_left_elbow_right_angle_is_90_deg():
    frame = _make_frame({11: (0.0, 0.0), 13: (1.0, 0.0), 15: (1.0, 1.0)})
    assert elbow_flexion_angle(frame, "left") == pytest.approx(90.0, abs=0.1)


def test_right_elbow_uses_landmarks_12_14_16():
    frame = _make_frame({12: (0.0, 0.0), 14: (1.0, 0.0), 16: (2.0, 0.0)})
    assert elbow_flexion_angle(frame, "right") == pytest.approx(180.0, abs=0.1)


def test_ignores_z_coordinate():
    frame = _make_frame({11: (0.0, 0.0), 13: (1.0, 0.0), 15: (2.0, 0.0)})
    frame.landmarks[11] = PoseLandmark(x=0.0, y=0.0, z=10.0, visibility=1.0, presence=1.0)
    frame.landmarks[13] = PoseLandmark(x=1.0, y=0.0, z=-5.0, visibility=1.0, presence=1.0)
    frame.landmarks[15] = PoseLandmark(x=2.0, y=0.0, z=7.5, visibility=1.0, presence=1.0)
    assert elbow_flexion_angle(frame, "left") == pytest.approx(180.0, abs=0.1)


def test_clamps_acos_argument_within_bounds():
    frame = _make_frame({11: (0.5, 0.5), 13: (0.5, 0.5), 15: (1.0, 0.0)})
    assert elbow_flexion_angle(frame, "left") == pytest.approx(0.0, abs=0.1)


def test_invalid_side_raises():
    frame = _make_frame({})
    with pytest.raises(ValueError):
        elbow_flexion_angle(frame, "middle")
