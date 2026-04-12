from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.ml.lifter import LiftedAngleTimeSeries
from auralink.ml.skeleton import NoOpSkeletonFitter, SkeletonBundle
from auralink.pipeline.stages.base import STAGE_NAME_SKELETON, StageContext
from auralink.pipeline.stages.skeleton import run_skeleton


def _ctx_with_lifted() -> StageContext:
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    frames = [Frame(timestamp_ms=i * 33, landmarks=[lm for _ in range(33)]) for i in range(3)]
    session = Session(
        metadata=SessionMetadata(movement="overhead_squat", device="t", model="t", frame_rate=30.0),
        frames=frames,
    )
    ctx = StageContext(session=session)
    ctx.artifacts["lift"] = LiftedAngleTimeSeries(
        angles={"left_knee_flexion": [180.0, 150.0, 120.0]},
        timestamps_ms=[0, 33, 66],
        scale_factor=0.3,
        is_3d=False,
    )
    return ctx


def test_stage_name_skeleton_constant_exists():
    assert STAGE_NAME_SKELETON == "skeleton"


def test_run_skeleton_reads_lift_artifact_and_returns_bundle():
    ctx = _ctx_with_lifted()
    result = run_skeleton(ctx)
    assert isinstance(result, SkeletonBundle)
    assert result.fitted is False
    assert result.params == {}


def test_run_skeleton_accepts_injected_fitter():
    ctx = _ctx_with_lifted()
    fitter = NoOpSkeletonFitter()
    result = run_skeleton(ctx, fitter=fitter)
    assert result.fitted is False
