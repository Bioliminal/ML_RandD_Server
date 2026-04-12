from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.ml.lifter import IdentityLifter, LiftedAngleTimeSeries
from auralink.pipeline.artifacts import NormalizedAngleTimeSeries
from auralink.pipeline.stages.base import STAGE_NAME_LIFT, StageContext
from auralink.pipeline.stages.lift import run_lift


def _ctx_with_normalized(
    angles: dict[str, list[float]],
    scale: float = 0.3,
) -> StageContext:
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    n = len(next(iter(angles.values())))
    frames = [Frame(timestamp_ms=i * 33, landmarks=[lm for _ in range(33)]) for i in range(n)]
    session = Session(
        metadata=SessionMetadata(movement="overhead_squat", device="t", model="t", frame_rate=30.0),
        frames=frames,
    )
    ctx = StageContext(session=session)
    ctx.artifacts["normalize"] = NormalizedAngleTimeSeries(
        angles=angles,
        timestamps_ms=[f.timestamp_ms for f in frames],
        scale_factor=scale,
    )
    return ctx


def test_stage_name_lift_constant_exists():
    assert STAGE_NAME_LIFT == "lift"


def test_run_lift_reads_normalize_artifact_and_returns_lifted():
    ctx = _ctx_with_normalized({"left_knee_flexion": [180.0, 150.0, 120.0]})
    result = run_lift(ctx)
    assert isinstance(result, LiftedAngleTimeSeries)
    assert result.angles == {"left_knee_flexion": [180.0, 150.0, 120.0]}
    assert result.scale_factor == 0.3
    assert result.is_3d is False


def test_run_lift_accepts_injected_lifter():
    ctx = _ctx_with_normalized({"trunk_lean": [1.0, 2.0]}, scale=0.5)
    custom = IdentityLifter()
    result = run_lift(ctx, lifter=custom)
    assert result.angles == {"trunk_lean": [1.0, 2.0]}
    assert result.scale_factor == 0.5
