"""Joint angle computation from BlazePose keypoints.

All angles in degrees. Functions accept a Frame and a side ("left" or "right")
and return the computed joint angle. The math operates in 2D (x, y) — z is
ignored at this scaffolding stage. 3D-aware versions come after MotionBERT
integration.
"""

from typing import Literal

import numpy as np

from auralink.api.schemas import Frame
from auralink.pose.keypoints import LandmarkIndex

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
