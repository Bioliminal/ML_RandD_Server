import numpy as np

from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.artifacts import NormalizedAngleTimeSeries
from auralink.pipeline.stages.base import StageContext
from auralink.pipeline.stages.rep_segment import (
    PRIMARY_REP_ANGLES_BY_MOVEMENT,
    run_rep_segment,
)


def _ctx_with_angles(movement: str, angle_lookup: dict[str, list[float]]) -> StageContext:
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    frames = [Frame(timestamp_ms=i * 33, landmarks=[lm for _ in range(33)]) for i in range(len(next(iter(angle_lookup.values()))))]
    session = Session(
        metadata=SessionMetadata(movement=movement, device="t", model="t", frame_rate=30.0),
        frames=frames,
    )
    ctx = StageContext(session=session)
    ctx.artifacts["normalize"] = NormalizedAngleTimeSeries(
        angles=angle_lookup,
        timestamps_ms=[f.timestamp_ms for f in frames],
        scale_factor=0.3,
    )
    return ctx


def test_rep_segment_identifies_two_reps_in_squat_pattern():
    descent = np.linspace(180, 90, 15).tolist()
    ascent = np.linspace(90, 180, 15).tolist()
    one_rep = descent + ascent
    series = one_rep + one_rep
    ctx = _ctx_with_angles(
        "overhead_squat",
        {"left_knee_flexion": series, "right_knee_flexion": series, "trunk_lean": [0.0] * len(series)},
    )
    result = run_rep_segment(ctx)
    assert "left_knee_flexion" in result.by_angle
    assert len(result.by_angle["left_knee_flexion"]) == 2
    assert len(result.by_angle["right_knee_flexion"]) == 2


def test_rep_segment_returns_empty_for_flat_signal():
    flat = [180.0] * 60
    ctx = _ctx_with_angles(
        "overhead_squat",
        {"left_knee_flexion": flat, "right_knee_flexion": flat, "trunk_lean": [0.0] * 60},
    )
    result = run_rep_segment(ctx)
    assert result.by_angle["left_knee_flexion"] == []


def test_primary_angles_table_covers_squat_movements():
    assert PRIMARY_REP_ANGLES_BY_MOVEMENT["overhead_squat"] == ("left_knee_flexion", "right_knee_flexion")
    assert PRIMARY_REP_ANGLES_BY_MOVEMENT["single_leg_squat"] == ("left_knee_flexion", "right_knee_flexion")
