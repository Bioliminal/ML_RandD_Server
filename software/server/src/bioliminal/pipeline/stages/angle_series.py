from bioliminal.api.schemas import Frame, MovementType
from bioliminal.pipeline.artifacts import AngleTimeSeries
from bioliminal.pipeline.stages.base import StageContext
from bioliminal.pose.joint_angles import (
    elbow_flexion_angle,
    hip_flexion_angle,
    knee_flexion_angle,
    knee_valgus_angle,
    trunk_lean_angle,
)


_SQUAT_TRACKED = (
    "left_knee_flexion",
    "right_knee_flexion",
    "left_hip_flexion",
    "right_hip_flexion",
    "left_knee_valgus",
    "right_knee_valgus",
    "trunk_lean",
)

_BICEP_TRACKED = (
    "left_elbow_flexion",
    "right_elbow_flexion",
)

_TRACKED_BY_MOVEMENT: dict[MovementType, tuple[str, ...]] = {
    "overhead_squat": _SQUAT_TRACKED,
    "single_leg_squat": _SQUAT_TRACKED,
    "push_up": _SQUAT_TRACKED,
    "rollup": _SQUAT_TRACKED,
    "bicep_curl": _BICEP_TRACKED,
}


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
    if name == "left_elbow_flexion":
        return elbow_flexion_angle(frame, "left")
    if name == "right_elbow_flexion":
        return elbow_flexion_angle(frame, "right")
    raise ValueError(f"unknown tracked angle: {name}")


def run_angle_series(ctx: StageContext) -> AngleTimeSeries:
    frames = ctx.session.frames
    timestamps = [f.timestamp_ms for f in frames]
    tracked = _TRACKED_BY_MOVEMENT.get(ctx.movement_type, _SQUAT_TRACKED)
    angles: dict[str, list[float]] = {
        name: [_compute_angle(name, f) for f in frames] for name in tracked
    }
    return AngleTimeSeries(angles=angles, timestamps_ms=timestamps)
