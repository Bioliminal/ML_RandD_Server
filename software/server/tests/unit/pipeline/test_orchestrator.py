import pytest

from bioliminal.api.schemas import Frame, Landmark, Session, SessionMetadata
from bioliminal.pipeline.artifacts import PipelineArtifacts
from bioliminal.pipeline.errors import PipelineError, QualityGateError, StageError
from bioliminal.pipeline.orchestrator import DEFAULT_REGISTRY, run_pipeline
from bioliminal.pipeline.registry import StageRegistry
from bioliminal.pipeline.stages.base import Stage


def _lm(vis: float = 1.0, pres: float = 1.0) -> Landmark:
    return Landmark(x=0.5, y=0.5, z=0.0, visibility=vis, presence=pres)


def _good_session(frame_count: int = 60) -> Session:
    frames = [
        Frame(timestamp_ms=i * 33, landmarks=[_lm() for _ in range(33)]) for i in range(frame_count)
    ]
    return Session(
        metadata=SessionMetadata(movement="overhead_squat", device="t", model="t", frame_rate=30.0),
        frames=frames,
    )


def test_default_registry_has_overhead_squat_and_single_leg_squat():
    assert DEFAULT_REGISTRY.has_movement("overhead_squat")
    assert DEFAULT_REGISTRY.has_movement("single_leg_squat")


def test_run_pipeline_produces_pipeline_artifacts_for_good_session():
    artifacts = run_pipeline(_good_session())
    assert isinstance(artifacts, PipelineArtifacts)
    assert artifacts.quality_report.passed is True
    assert artifacts.angle_series is not None
    assert artifacts.normalized_angle_series is not None
    assert artifacts.rep_boundaries is not None
    assert artifacts.per_rep_metrics is not None
    assert artifacts.within_movement_trend is not None


def test_run_pipeline_raises_quality_gate_error_on_bad_session():
    bad = Session(
        metadata=SessionMetadata(movement="overhead_squat", device="t", model="t", frame_rate=10.0),
        frames=_good_session(30).frames,
    )
    with pytest.raises(QualityGateError) as exc:
        run_pipeline(bad)
    assert any(issue.code == "low_frame_rate" for issue in exc.value.report.issues)


def test_run_pipeline_wraps_unexpected_stage_failure_as_stage_error():
    reg = StageRegistry()

    def _boom(_ctx):
        raise RuntimeError("boom")

    reg.register_movement(
        "overhead_squat",
        [Stage(name="quality_gate", run=lambda c: _pass()), Stage(name="angle_series", run=_boom)],
    )
    with pytest.raises(StageError) as exc:
        run_pipeline(_good_session(), registry=reg)
    assert exc.value.stage_name == "angle_series"


def _pass():
    from bioliminal.pipeline.artifacts import SessionQualityReport

    return SessionQualityReport(passed=True, issues=[], metrics={})


def test_run_pipeline_unknown_movement_raises_pipeline_error():
    reg = StageRegistry()
    with pytest.raises(PipelineError):
        run_pipeline(_good_session(), registry=reg)


def test_default_registry_has_push_up_and_rollup():
    assert DEFAULT_REGISTRY.has_movement("push_up")
    assert DEFAULT_REGISTRY.has_movement("rollup")


def test_run_pipeline_populates_lift_and_skeleton_for_overhead_squat():
    artifacts = run_pipeline(_good_session())
    assert artifacts.lift_result is not None
    assert artifacts.lift_result.is_3d is False
    assert artifacts.skeleton_result is not None
    assert artifacts.skeleton_result.fitted is False
    assert artifacts.per_rep_metrics is not None  # rep path still runs
    assert artifacts.phase_boundaries is None


def test_run_pipeline_populates_lift_skeleton_for_push_up():
    session = Session(
        metadata=SessionMetadata(movement="push_up", device="t", model="t", frame_rate=30.0),
        frames=_good_session(60).frames,
    )
    artifacts = run_pipeline(session)
    assert artifacts.lift_result is not None
    assert artifacts.skeleton_result is not None
    # push_up pipeline stops at skeleton — rep-based stages require
    # elbow_flexion angle which will be added in a follow-on epoch.
    # Registering push_up with _default_stage_list() would silently
    # produce empty reps because rep_segment's PRIMARY_REP_ANGLES_BY_MOVEMENT
    # dict only covers knee-flexion movements. Per L1 principle 4
    # (movement-type dispatch via strategy pattern) push_up gets its
    # own stage list rather than hiding the gap behind default registration.
    assert artifacts.rep_boundaries is None
    assert artifacts.per_rep_metrics is None
    assert artifacts.within_movement_trend is None
    assert artifacts.phase_boundaries is None


def test_run_pipeline_rollup_uses_phase_segment_not_rep_segment():
    session = Session(
        metadata=SessionMetadata(movement="rollup", device="t", model="t", frame_rate=30.0),
        frames=_good_session(60).frames,
    )
    artifacts = run_pipeline(session)
    assert artifacts.lift_result is not None
    assert artifacts.skeleton_result is not None
    assert artifacts.phase_boundaries is not None
    assert len(artifacts.phase_boundaries.phases) == 1
    assert artifacts.phase_boundaries.phases[0].label == "full_movement"
    # rollup pipeline skips rep-based stages
    assert artifacts.rep_boundaries is None
    assert artifacts.per_rep_metrics is None
    assert artifacts.within_movement_trend is None
