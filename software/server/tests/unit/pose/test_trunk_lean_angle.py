import pytest

from auralink.api.schemas import Frame, Landmark
from auralink.pose.joint_angles import trunk_lean_angle


def _frame_with(left_sh, right_sh, left_hip, right_hip) -> Frame:
    base = [Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0, presence=1.0) for _ in range(33)]
    base[11] = Landmark(x=left_sh[0], y=left_sh[1], z=0.0, visibility=1.0, presence=1.0)
    base[12] = Landmark(x=right_sh[0], y=right_sh[1], z=0.0, visibility=1.0, presence=1.0)
    base[23] = Landmark(x=left_hip[0], y=left_hip[1], z=0.0, visibility=1.0, presence=1.0)
    base[24] = Landmark(x=right_hip[0], y=right_hip[1], z=0.0, visibility=1.0, presence=1.0)
    return Frame(timestamp_ms=0, landmarks=base)


def test_trunk_vertical_is_zero():
    frame = _frame_with(
        left_sh=(0.45, 0.3), right_sh=(0.55, 0.3),
        left_hip=(0.45, 0.5), right_hip=(0.55, 0.5),
    )
    assert trunk_lean_angle(frame) == pytest.approx(0.0, abs=1e-6)


def test_trunk_leaning_forward_45_degrees():
    frame = _frame_with(
        left_sh=(0.65, 0.35), right_sh=(0.75, 0.35),
        left_hip=(0.45, 0.55), right_hip=(0.55, 0.55),
    )
    assert trunk_lean_angle(frame) == pytest.approx(45.0, abs=1.0)


def test_trunk_with_zero_length_trunk_returns_zero():
    frame = _frame_with(
        left_sh=(0.5, 0.5), right_sh=(0.5, 0.5),
        left_hip=(0.5, 0.5), right_hip=(0.5, 0.5),
    )
    assert trunk_lean_angle(frame) == 0.0
