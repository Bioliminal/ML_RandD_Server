"""Joint angle computation from BlazePose keypoints.

All angles in degrees. Functions accept a Frame and a side ("left" or "right")
and return the computed joint angle. The math operates in 2D (x, y) — z is
ignored at this scaffolding stage. 3D-aware versions come after MotionBERT
integration.
"""

from typing import Literal

import numpy as np

from bioliminal.api.schemas import Frame
from bioliminal.pose.keypoints import LandmarkIndex

Side = Literal["left", "right"]


def _xy(frame: Frame, idx: int) -> np.ndarray:
    lm = frame.landmarks[idx]
    return np.array([lm.x, lm.y], dtype=np.float64)


def angle_between_points(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Return angle ABC in degrees — the angle at vertex B."""
    ba = a - b
    bc = c - b
    ba_norm = np.linalg.norm(ba)
    bc_norm = np.linalg.norm(bc)
    if ba_norm == 0 or bc_norm == 0:
        return 0.0
    cos_angle = np.dot(ba, bc) / (ba_norm * bc_norm)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


def knee_flexion_angle(frame: Frame, side: Side) -> float:
    """Knee flexion angle — hip-knee-ankle. 180° = straight leg."""
    if side == "left":
        hip_idx = LandmarkIndex.LEFT_HIP
        knee_idx = LandmarkIndex.LEFT_KNEE
        ankle_idx = LandmarkIndex.LEFT_ANKLE
    else:
        hip_idx = LandmarkIndex.RIGHT_HIP
        knee_idx = LandmarkIndex.RIGHT_KNEE
        ankle_idx = LandmarkIndex.RIGHT_ANKLE
    return angle_between_points(
        _xy(frame, hip_idx),
        _xy(frame, knee_idx),
        _xy(frame, ankle_idx),
    )


def hip_flexion_angle(frame: Frame, side: Side) -> float:
    """Hip flexion angle — shoulder-hip-knee. 180° = standing upright."""
    if side == "left":
        shoulder_idx = LandmarkIndex.LEFT_SHOULDER
        hip_idx = LandmarkIndex.LEFT_HIP
        knee_idx = LandmarkIndex.LEFT_KNEE
    else:
        shoulder_idx = LandmarkIndex.RIGHT_SHOULDER
        hip_idx = LandmarkIndex.RIGHT_HIP
        knee_idx = LandmarkIndex.RIGHT_KNEE
    return angle_between_points(
        _xy(frame, shoulder_idx),
        _xy(frame, hip_idx),
        _xy(frame, knee_idx),
    )


def knee_valgus_angle(frame: Frame, side: Side) -> float:
    """Knee valgus — angle between hip->knee and hip->ankle vectors.

    0 degrees = knee lies on the hip-ankle ray (neutral alignment).
    Positive values indicate the knee has shifted off-line; for a frontal
    camera view this approximates medial collapse (valgus) for small
    deviations. Not a true perpendicular-distance measurement.

    This is a 2D approximation in the coronal plane — camera must be positioned
    frontally for the measurement to be meaningful. The 3D-aware version lands
    after MotionBERT integration.
    """
    if side == "left":
        hip_idx = LandmarkIndex.LEFT_HIP
        knee_idx = LandmarkIndex.LEFT_KNEE
        ankle_idx = LandmarkIndex.LEFT_ANKLE
    else:
        hip_idx = LandmarkIndex.RIGHT_HIP
        knee_idx = LandmarkIndex.RIGHT_KNEE
        ankle_idx = LandmarkIndex.RIGHT_ANKLE

    hip = _xy(frame, hip_idx)
    knee = _xy(frame, knee_idx)
    ankle = _xy(frame, ankle_idx)

    hip_to_ankle = ankle - hip
    hip_to_knee = knee - hip

    hip_ankle_norm = np.linalg.norm(hip_to_ankle)
    hip_knee_norm = np.linalg.norm(hip_to_knee)
    if hip_ankle_norm == 0 or hip_knee_norm == 0:
        return 0.0

    cos_angle = np.dot(hip_to_ankle, hip_to_knee) / (hip_ankle_norm * hip_knee_norm)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


def trunk_lean_angle(frame: Frame) -> float:
    """Trunk lean — angle between the trunk axis and the image vertical.

    Trunk axis = shoulder midpoint minus hip midpoint. Vertical is (0, -1)
    because image y increases downward. Returned in degrees, always >= 0.
    """
    l_sh = _xy(frame, LandmarkIndex.LEFT_SHOULDER)
    r_sh = _xy(frame, LandmarkIndex.RIGHT_SHOULDER)
    l_hip = _xy(frame, LandmarkIndex.LEFT_HIP)
    r_hip = _xy(frame, LandmarkIndex.RIGHT_HIP)
    shoulder_mid = (l_sh + r_sh) / 2.0
    hip_mid = (l_hip + r_hip) / 2.0
    trunk = shoulder_mid - hip_mid
    norm = float(np.linalg.norm(trunk))
    if norm == 0.0:
        return 0.0
    vertical = np.array([0.0, -1.0], dtype=np.float64)
    cos_angle = float(np.dot(trunk, vertical) / norm)
    cos_angle = max(-1.0, min(1.0, cos_angle))
    return float(np.degrees(np.arccos(cos_angle)))
