import math
import pytest

from bioliminal.api.schemas import Session, SessionMetadata
from bioliminal.pipeline.artifacts import (
    NormalizedAngleTimeSeries,
    RepBoundaries,
    RepBoundaryModel,
)
from bioliminal.pipeline.stages.base import StageContext
from bioliminal.pipeline.stages.per_rep_metrics import run_per_rep_metrics


def _cosine_curl(n_reps: int, samples_per_rep: int, peak: float, ext: float) -> list[float]:
    mid = (peak + ext) / 2.0
    amp = (ext - peak) / 2.0
    return [
        mid + amp * math.cos(2 * math.pi * (i % samples_per_rep) / samples_per_rep)
        for i in range(n_reps * samples_per_rep)
    ]


def _mk_ctx(series: list[float], reps: list[RepBoundaryModel], *, fps: float = 30.0) -> StageContext:
    session = Session(
        metadata=SessionMetadata(
            movement="bicep_curl", device="t", model="m", frame_rate=fps
        ),
        frames=[],
    )
    artifacts = {
        "normalize": NormalizedAngleTimeSeries(
            angles={"left_elbow_flexion": series, "right_elbow_flexion": series},
            timestamps_ms=list(range(len(series))),
            scale_factor=1.0,
        ),
        "rep_segment": RepBoundaries(
            by_angle={"left_elbow_flexion": reps, "right_elbow_flexion": reps}
        ),
    }
    return StageContext(session=session, artifacts=artifacts)


def test_bicep_per_rep_metrics_amplitude_matches_boundary_swing():
    series = _cosine_curl(n_reps=10, samples_per_rep=90, peak=30.0, ext=170.0)
    reps = [
        RepBoundaryModel(
            start_index=i * 90,
            bottom_index=i * 90 + 45,
            end_index=(i + 1) * 90,
            start_angle=170.0, bottom_angle=30.0, end_angle=170.0,
        )
        for i in range(10)
    ]
    series.append(170.0)
    ctx = _mk_ctx(series, reps)
    result = run_per_rep_metrics(ctx)
    assert result.primary_angle == "left_elbow_flexion"
    assert len(result.reps) == 10
    for rm in result.reps:
        assert rm.amplitude_deg == pytest.approx(140.0, abs=0.1)


def test_bicep_per_rep_metrics_tempo_seconds():
    series = _cosine_curl(10, 90, 30.0, 170.0) + [170.0]
    reps = [
        RepBoundaryModel(
            start_index=i * 90, bottom_index=i * 90 + 45, end_index=(i + 1) * 90,
            start_angle=170.0, bottom_angle=30.0, end_angle=170.0,
        ) for i in range(10)
    ]
    ctx = _mk_ctx(series, reps, fps=30.0)
    result = run_per_rep_metrics(ctx)
    for rm in result.reps:
        assert rm.concentric_s == pytest.approx(1.5, abs=0.05)
        assert rm.eccentric_s == pytest.approx(1.5, abs=0.05)


def test_bicep_per_rep_metrics_peak_velocity_positive():
    series = _cosine_curl(10, 90, 30.0, 170.0) + [170.0]
    reps = [
        RepBoundaryModel(
            start_index=i * 90, bottom_index=i * 90 + 45, end_index=(i + 1) * 90,
            start_angle=170.0, bottom_angle=30.0, end_angle=170.0,
        ) for i in range(10)
    ]
    ctx = _mk_ctx(series, reps, fps=30.0)
    result = run_per_rep_metrics(ctx)
    for rm in result.reps:
        assert rm.peak_velocity_deg_per_s > 0.0


def test_bicep_session_scalar_cv_on_uniform_reps_is_small():
    series = _cosine_curl(10, 90, 30.0, 170.0) + [170.0]
    reps = [
        RepBoundaryModel(
            start_index=i * 90, bottom_index=i * 90 + 45, end_index=(i + 1) * 90,
            start_angle=170.0, bottom_angle=30.0, end_angle=170.0,
        ) for i in range(10)
    ]
    ctx = _mk_ctx(series, reps, fps=30.0)
    result = run_per_rep_metrics(ctx)
    for rm in result.reps:
        assert rm.amplitude_cv_pct == pytest.approx(0.0, abs=0.5)
        assert rm.tempo_cv_pct == pytest.approx(0.0, abs=0.5)


def test_bicep_velocity_decline_pct_from_decreasing_amplitudes():
    rep_amps = [140 - i * 10 for i in range(10)]
    samples_per_rep = 90
    series: list[float] = []
    for amp in rep_amps:
        peak = 170.0 - amp
        mid = (peak + 170.0) / 2.0
        hamp = (170.0 - peak) / 2.0
        for i in range(samples_per_rep):
            series.append(mid + hamp * math.cos(2 * math.pi * i / samples_per_rep))
    series.append(170.0)
    reps = []
    for i, amp in enumerate(rep_amps):
        start = i * samples_per_rep
        reps.append(RepBoundaryModel(
            start_index=start,
            bottom_index=start + samples_per_rep // 2,
            end_index=(i + 1) * samples_per_rep,
            start_angle=170.0, bottom_angle=170.0 - amp, end_angle=170.0,
        ))
    ctx = _mk_ctx(series, reps, fps=30.0)
    result = run_per_rep_metrics(ctx)
    for rm in result.reps:
        assert rm.velocity_decline_pct is not None
        assert rm.velocity_decline_pct > 0.3


def test_squat_movement_still_populates_knee_metrics_only():
    from bioliminal.pipeline.artifacts import NormalizedAngleTimeSeries
    series = [10.0, 30.0, 100.0, 30.0, 10.0]
    reps = [RepBoundaryModel(
        start_index=0, bottom_index=2, end_index=4,
        start_angle=10.0, bottom_angle=100.0, end_angle=10.0
    )]
    session = Session(
        metadata=SessionMetadata(movement="overhead_squat", device="t", model="m", frame_rate=30.0),
        frames=[],
    )
    artifacts = {
        "normalize": NormalizedAngleTimeSeries(
            angles={
                "left_knee_flexion": series,
                "trunk_lean": [0.0] * 5,
                "left_knee_valgus": [0.0] * 5,
                "right_knee_valgus": [0.0] * 5,
            },
            timestamps_ms=[0, 33, 66, 99, 132],
            scale_factor=1.0,
        ),
        "rep_segment": RepBoundaries(by_angle={"left_knee_flexion": reps}),
    }
    ctx = StageContext(session=session, artifacts=artifacts)
    result = run_per_rep_metrics(ctx)
    assert result.primary_angle == "left_knee_flexion"
    for rm in result.reps:
        assert rm.concentric_s is None
        assert rm.velocity_decline_pct is None
