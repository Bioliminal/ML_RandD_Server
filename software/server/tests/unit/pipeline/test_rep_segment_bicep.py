import pytest

from bioliminal.pipeline.artifacts import NormalizedAngleTimeSeries
from bioliminal.pipeline.stages.base import StageContext
from bioliminal.pipeline.stages.rep_segment import run_rep_segment


def _synthetic_elbow_series(
    *, n_reps: int, samples_per_rep: int, peak_flexion: float, full_extension: float
) -> list[float]:
    """Cosine-shaped curl: starts extended, flexes to peak, returns extended."""
    import math
    series: list[float] = []
    mid = full_extension
    amp = (full_extension - peak_flexion) / 2.0
    for _ in range(n_reps):
        for i in range(samples_per_rep):
            series.append(mid + amp * math.cos(2 * math.pi * i / samples_per_rep) - amp)
    series.append(full_extension)
    return series


def _mk_ctx(movement: str, elbow_series: list[float]) -> StageContext:
    from bioliminal.api.schemas import Session, SessionMetadata
    session = Session(
        metadata=SessionMetadata(
            movement=movement, device="t", model="m", frame_rate=30.0
        ),
        frames=[],
    )
    artifacts = {
        "normalize": NormalizedAngleTimeSeries(
            angles={"left_elbow_flexion": elbow_series, "right_elbow_flexion": elbow_series},
            timestamps_ms=list(range(len(elbow_series))),
            scale_factor=1.0,
        )
    }
    return StageContext(session=session, artifacts=artifacts)


def test_bicep_curl_segments_10_reps_from_clean_sine():
    series = _synthetic_elbow_series(
        n_reps=10, samples_per_rep=90, peak_flexion=30.0, full_extension=170.0
    )
    ctx = _mk_ctx("bicep_curl", series)
    reps = run_rep_segment(ctx)
    assert "left_elbow_flexion" in reps.by_angle
    assert len(reps.by_angle["left_elbow_flexion"]) == 10


def test_held_position_does_not_count_as_rep():
    series = [170.0] * 30 + [90.0] * 60 + [170.0] * 30
    ctx = _mk_ctx("bicep_curl", series)
    reps = run_rep_segment(ctx)
    assert len(reps.by_angle["left_elbow_flexion"]) == 1


def test_micro_jitter_does_not_double_count():
    series = _synthetic_elbow_series(
        n_reps=10, samples_per_rep=90, peak_flexion=30.0, full_extension=170.0
    )
    jittered = [v + (5.0 if i % 45 == 0 else 0.0) for i, v in enumerate(series)]
    ctx = _mk_ctx("bicep_curl", jittered)
    reps = run_rep_segment(ctx)
    assert len(reps.by_angle["left_elbow_flexion"]) == 10
