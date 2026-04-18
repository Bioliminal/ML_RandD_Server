import math
from pathlib import Path

import pytest

from bioliminal.api.schemas import Frame, Landmark, Session, SessionMetadata
from bioliminal.pipeline.artifacts import (
    MovementTemporalSummary,
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    RepBoundaries,
    RepBoundaryModel,
    RepMetric,
)
from bioliminal.pipeline.stages.base import StageContext
from bioliminal.pipeline.stages.rep_comparison import run_rep_comparison


def _make_session(movement: str) -> Session:
    lm = [Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0) for _ in range(33)]
    frame = Frame(timestamp_ms=0, landmarks=lm)
    return Session(
        metadata=SessionMetadata(
            movement=movement,  # type: ignore[arg-type]
            device="test",
            model="test",
            frame_rate=30.0,
        ),
        frames=[frame],
    )


def _cosine_trace(n: int = 30, amplitude: float = 45.0, offset: float = 135.0) -> list[float]:
    return [offset + amplitude * math.cos(2.0 * math.pi * i / n) for i in range(n)]


def _write_reference_rep(
    tmp_path: Path, movement: str, angle_name: str, series: list[float]
) -> None:
    import json

    (tmp_path / f"{movement}.json").write_text(
        json.dumps(
            {
                "movement": movement,
                "angles": {angle_name: series},
                "frame_rate": 30.0,
                "frames_per_rep": len(series),
            }
        )
    )


def _build_ctx(
    movement: str, primary_angle: str, user_series: list[float], n_reps: int
) -> StageContext:
    ctx = StageContext(session=_make_session(movement))
    full_trace: list[float] = []
    boundaries: list[RepBoundaryModel] = []
    for _r in range(n_reps):
        start = len(full_trace)
        full_trace.extend(user_series)
        end = len(full_trace) - 1
        boundaries.append(
            RepBoundaryModel(
                start_index=start,
                bottom_index=start + len(user_series) // 2,
                end_index=end,
                start_angle=user_series[0],
                bottom_angle=min(user_series),
                end_angle=user_series[-1],
            )
        )
    ctx.artifacts["normalize"] = NormalizedAngleTimeSeries(
        angles={primary_angle: full_trace},
        timestamps_ms=list(range(len(full_trace))),
        scale_factor=1.0,
    )
    ctx.artifacts["rep_segment"] = RepBoundaries(by_angle={primary_angle: boundaries})
    ctx.artifacts["per_rep_metrics"] = PerRepMetrics(
        primary_angle=primary_angle,
        reps=[
            RepMetric(
                rep_index=i,
                amplitude_deg=90.0,
                peak_velocity_deg_per_s=10.0,
                rom_deg=90.0,
                mean_trunk_lean_deg=4.0,
                mean_knee_valgus_deg=2.0,
            )
            for i in range(n_reps)
        ],
    )
    return ctx


@pytest.fixture(autouse=True)
def _patch_config_dirs(tmp_path, monkeypatch):
    ref_dir = tmp_path / "reference_reps"
    ref_dir.mkdir()
    thr_path = tmp_path / "thresholds.yaml"
    thr_path.write_text("""
ncc_clean_min: 0.95
ncc_concern_min: 0.75
rom_deviation_concern_pct: 15.0
rom_deviation_flag_pct: 25.0
form_drift_ncc_slope_threshold: -0.02
form_drift_rom_mean_deviation_pct: 15.0
""")
    import bioliminal.temporal.reference_reps as ref_mod
    import bioliminal.temporal.threshold_loader as thr_mod

    monkeypatch.setattr(ref_mod, "_DEFAULT_CONFIG_DIR", ref_dir)
    monkeypatch.setattr(thr_mod, "_DEFAULT_PATH", thr_path)
    return {"ref_dir": ref_dir}


def test_stage_produces_summary_for_matching_reps(tmp_path, _patch_config_dirs):
    ref_dir = _patch_config_dirs["ref_dir"]
    ref_series = _cosine_trace()
    _write_reference_rep(ref_dir, "overhead_squat", "left_knee_flexion", ref_series)

    ctx = _build_ctx("overhead_squat", "left_knee_flexion", ref_series, n_reps=3)
    summary = run_rep_comparison(ctx)
    assert isinstance(summary, MovementTemporalSummary)
    assert summary.primary_angle == "left_knee_flexion"
    assert len(summary.rep_comparisons) == 3
    assert all(c.status == "clean" for c in summary.rep_comparisons)
    assert summary.form_drift_detected is False


def test_stage_raises_when_reference_missing(_patch_config_dirs):
    ref_series = _cosine_trace()
    ctx = _build_ctx("overhead_squat", "left_knee_flexion", ref_series, n_reps=1)
    with pytest.raises(FileNotFoundError):
        run_rep_comparison(ctx)


def test_stage_uses_primary_angle_from_per_rep_metrics(tmp_path, _patch_config_dirs):
    ref_dir = _patch_config_dirs["ref_dir"]
    ref_series = _cosine_trace()
    _write_reference_rep(ref_dir, "single_leg_squat", "left_knee_flexion", ref_series)

    ctx = _build_ctx("single_leg_squat", "left_knee_flexion", ref_series, n_reps=2)
    summary = run_rep_comparison(ctx)
    assert summary.primary_angle == "left_knee_flexion"


def test_stage_raises_when_reference_missing_primary_angle(tmp_path, _patch_config_dirs):
    ref_dir = _patch_config_dirs["ref_dir"]
    _write_reference_rep(ref_dir, "overhead_squat", "right_knee_flexion", _cosine_trace())

    ctx = _build_ctx("overhead_squat", "left_knee_flexion", _cosine_trace(), n_reps=1)
    with pytest.raises(KeyError):
        run_rep_comparison(ctx)
