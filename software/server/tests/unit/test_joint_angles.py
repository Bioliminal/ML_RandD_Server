import math

import numpy as np
import pytest

from auralink.api.schemas import Frame, Landmark
from auralink.pose.joint_angles import (
    angle_between_points,
    hip_flexion_angle,
    knee_flexion_angle,
)


def _lm(x: float, y: float, z: float = 0.0) -> Landmark:
    return Landmark(x=x, y=y, z=z, visibility=1.0, presence=1.0)


def _frame_with_overrides(overrides: dict[int, Landmark]) -> Frame:
    default = _lm(0.5, 0.5)
    landmarks = [overrides.get(i, default) for i in range(33)]
    return Frame(timestamp_ms=0, landmarks=landmarks)


def test_angle_between_points_90_degrees():
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 0.0])
    c = np.array([0.0, 1.0])
    assert angle_between_points(a, b, c) == pytest.approx(90.0, abs=0.01)


def test_angle_between_points_180_degrees():
    a = np.array([0.0, 0.0])
    b = np.array([1.0, 0.0])
    c = np.array([2.0, 0.0])
    assert angle_between_points(a, b, c) == pytest.approx(180.0, abs=0.01)


def test_angle_between_points_45_degrees():
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 0.0])
    c = np.array([1.0, 1.0])
    assert angle_between_points(a, b, c) == pytest.approx(45.0, abs=0.01)


def test_knee_flexion_straight_leg():
    frame = _frame_with_overrides({
        23: _lm(0.5, 0.3),
        25: _lm(0.5, 0.5),
        27: _lm(0.5, 0.7),
    })
    assert knee_flexion_angle(frame, side="left") == pytest.approx(180.0, abs=0.5)


def test_knee_flexion_90_degrees():
    frame = _frame_with_overrides({
        23: _lm(0.5, 0.3),
        25: _lm(0.5, 0.5),
        27: _lm(0.7, 0.5),
    })
    assert knee_flexion_angle(frame, side="left") == pytest.approx(90.0, abs=0.5)


def test_hip_flexion_standing():
    frame = _frame_with_overrides({
        11: _lm(0.5, 0.1),
        23: _lm(0.5, 0.4),
        25: _lm(0.5, 0.7),
    })
    assert hip_flexion_angle(frame, side="left") == pytest.approx(180.0, abs=0.5)


def test_hip_flexion_seated():
    frame = _frame_with_overrides({
        11: _lm(0.5, 0.1),
        23: _lm(0.5, 0.4),
        25: _lm(0.8, 0.4),
    })
    assert hip_flexion_angle(frame, side="left") == pytest.approx(90.0, abs=0.5)
