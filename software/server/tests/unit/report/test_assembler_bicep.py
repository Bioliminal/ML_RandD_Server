import pytest

from bioliminal.pipeline.artifacts import (
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    RepBoundaries,
    RepBoundaryModel,
    RepMetric,
)
from bioliminal.report.assembler import assemble_rep_scores


def _mk_rep_metric(idx: int) -> RepMetric:
    return RepMetric(
        rep_index=idx,
        amplitude_deg=140.0,
        peak_velocity_deg_per_s=200.0,
        rom_deg=140.0,
        mean_trunk_lean_deg=0.0,
        mean_knee_valgus_deg=0.0,
        concentric_s=1.5,
        eccentric_s=1.5,
        velocity_decline_pct=0.05,
        amplitude_cv_pct=2.0,
        tempo_cv_pct=2.0,
    )


def test_bicep_rep_scores_populate_elbow_angle_range():
    angles = [170.0, 100.0, 30.0, 100.0, 170.0, 100.0, 30.0, 100.0, 170.0]
    normalized = NormalizedAngleTimeSeries(
        angles={"left_elbow_flexion": angles, "right_elbow_flexion": angles},
        timestamps_ms=[i * 33 for i in range(len(angles))],
        scale_factor=1.0,
    )
    boundaries = RepBoundaries(by_angle={
        "left_elbow_flexion": [
            RepBoundaryModel(start_index=0, bottom_index=2, end_index=4,
                             start_angle=170.0, bottom_angle=30.0, end_angle=170.0),
            RepBoundaryModel(start_index=4, bottom_index=6, end_index=8,
                             start_angle=170.0, bottom_angle=30.0, end_angle=170.0),
        ]
    })
    per_rep = PerRepMetrics(
        primary_angle="left_elbow_flexion",
        reps=[_mk_rep_metric(0), _mk_rep_metric(1)],
    )

    rep_scores = assemble_rep_scores(
        per_rep=per_rep,
        normalized=normalized,
        boundaries=boundaries,
        movement_type="bicep_curl",
    )
    assert len(rep_scores) == 2
    for rs in rep_scores:
        assert rs.elbow_angle_range is not None
        lo, hi = rs.elbow_angle_range
        assert lo == pytest.approx(30.0, abs=0.1)
        assert hi == pytest.approx(170.0, abs=0.1)


def test_squat_rep_scores_leave_elbow_angle_range_none():
    normalized = NormalizedAngleTimeSeries(
        angles={"left_knee_flexion": [10.0, 100.0, 10.0]},
        timestamps_ms=[0, 33, 66],
        scale_factor=1.0,
    )
    boundaries = RepBoundaries(by_angle={
        "left_knee_flexion": [
            RepBoundaryModel(start_index=0, bottom_index=1, end_index=2,
                             start_angle=10.0, bottom_angle=100.0, end_angle=10.0),
        ]
    })
    per_rep = PerRepMetrics(
        primary_angle="left_knee_flexion",
        reps=[RepMetric(
            rep_index=0, amplitude_deg=90.0, peak_velocity_deg_per_s=50.0,
            rom_deg=90.0, mean_trunk_lean_deg=0.0, mean_knee_valgus_deg=0.0,
        )],
    )
    rep_scores = assemble_rep_scores(
        per_rep=per_rep, normalized=normalized, boundaries=boundaries,
        movement_type="overhead_squat",
    )
    assert rep_scores[0].elbow_angle_range is None
