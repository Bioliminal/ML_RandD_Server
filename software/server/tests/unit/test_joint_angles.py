import math

import numpy as np
import pytest

from auralink.api.schemas import Frame, Landmark
from auralink.pose.joint_angles import (
    angle_between_points,
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
