import pytest

from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.artifacts import PipelineArtifacts
from auralink.pipeline.errors import PipelineError, QualityGateError, StageError
from auralink.pipeline.orchestrator import DEFAULT_REGISTRY, run_pipeline
from auralink.pipeline.registry import StageRegistry
from auralink.pipeline.stages.base import Stage


def _lm(vis: float = 1.0, pres: float = 1.0) -> Landmark:
    return Landmark(x=0.5, y=0.5, z=0.0, visibility=vis, presence=pres)


def _good_session(frame_count: int = 60) -> Session:
    frames = [Frame(timestamp_ms=i * 33, landmarks=[_lm() for _ in range(33)]) for i in range(frame_count)]
    return Session(
        metadata=SessionMetadata(
            movement="overhead_squat", device="t", model="t", frame_rate=30.0
        ),
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
        metadata=SessionMetadata(
            movement="overhead_squat", device="t", model="t", frame_rate=10.0
        ),
        frames=_good_session(30).frames,
    )
    with pytest.raises(QualityGateError) as exc:
        run_pipeline(bad)
    assert any(issue.code == "low_frame_rate" for issue in exc.value.report.issues)


def test_run_pipeline_wraps_unexpected_stage_failure_as_stage_error():
    reg = StageRegistry()
    def _boom(_ctx):
        raise RuntimeError("boom")
    reg.register_movement("overhead_squat", [Stage(name="quality_gate", run=lambda c: _pass()), Stage(name="angle_series", run=_boom)])
    with pytest.raises(StageError) as exc:
        run_pipeline(_good_session(), registry=reg)
    assert exc.value.stage_name == "angle_series"


def _pass():
    from auralink.pipeline.artifacts import SessionQualityReport
    return SessionQualityReport(passed=True, issues=[], metrics={})


def test_run_pipeline_unknown_movement_raises_pipeline_error():
    reg = StageRegistry()
    with pytest.raises(PipelineError):
        run_pipeline(_good_session(), registry=reg)
