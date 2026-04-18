from bioliminal.api.schemas import Frame
from bioliminal.pipeline.artifacts import AngleTimeSeries
from bioliminal.pipeline.stages.base import StageContext
from bioliminal.pose.joint_angles import (
    hip_flexion_angle,
    knee_flexion_angle,
    knee_valgus_angle,
    trunk_lean_angle,
)

TRACKED_ANGLE_NAMES = (
    "left_knee_flexion",
    "right_knee_flexion",
    "left_hip_flexion",
    "right_hip_flexion",
    "left_knee_valgus",
    "right_knee_valgus",
    "trunk_lean",
)


def _compute_angle(name: str, frame: Frame) -> float:
    if name == "left_knee_flexion":
        return knee_flexion_angle(frame, "left")
    if name == "right_knee_flexion":
        return knee_flexion_angle(frame, "right")
    if name == "left_hip_flexion":
        return hip_flexion_angle(frame, "left")
    if name == "right_hip_flexion":
        return hip_flexion_angle(frame, "right")
    if name == "left_knee_valgus":
        return knee_valgus_angle(frame, "left")
    if name == "right_knee_valgus":
        return knee_valgus_angle(frame, "right")
    if name == "trunk_lean":
        return trunk_lean_angle(frame)
    raise ValueError(f"unknown tracked angle: {name}")


def run_angle_series(ctx: StageContext) -> AngleTimeSeries:
    frames = ctx.session.frames
    timestamps = [f.timestamp_ms for f in frames]
    angles: dict[str, list[float]] = {
        name: [_compute_angle(name, f) for f in frames] for name in TRACKED_ANGLE_NAMES
    }
    return AngleTimeSeries(angles=angles, timestamps_ms=timestamps)
