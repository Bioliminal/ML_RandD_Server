import pytest
from pydantic import ValidationError

from auralink.pipeline.artifacts import (
    AngleTimeSeries,
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    PipelineArtifacts,
    QualityIssue,
    RepBoundaries,
    RepBoundaryModel,
    RepMetric,
    SessionQualityReport,
    WithinMovementTrend,
)


def test_quality_issue_requires_code_and_detail():
    issue = QualityIssue(code="low_frame_rate", detail="23.4 < 25")
    assert issue.code == "low_frame_rate"
    assert issue.detail == "23.4 < 25"


def test_session_quality_report_defaults_pass_when_empty():
    report = SessionQualityReport(passed=True, issues=[], metrics={"frame_rate": 30.0})
    assert report.passed is True
    assert report.metrics["frame_rate"] == 30.0


def test_angle_time_series_shape():
    series = AngleTimeSeries(
        angles={"left_knee_flexion": [180.0, 150.0, 120.0]},
        timestamps_ms=[0, 33, 66],
    )
    assert series.angles["left_knee_flexion"][1] == 150.0
    assert len(series.timestamps_ms) == 3


def test_normalized_angle_time_series_requires_scale_factor():
    normalized = NormalizedAngleTimeSeries(
        angles={"trunk_lean": [2.0]},
        timestamps_ms=[0],
        scale_factor=0.25,
    )
    assert normalized.scale_factor == 0.25
    with pytest.raises(ValidationError):
        NormalizedAngleTimeSeries(angles={}, timestamps_ms=[])


def test_rep_boundary_model_indices_must_be_non_negative():
    rep = RepBoundaryModel(
        start_index=0, bottom_index=14, end_index=29,
        start_angle=180.0, bottom_angle=90.0, end_angle=180.0,
    )
    assert rep.end_index == 29
    with pytest.raises(ValidationError):
        RepBoundaryModel(
            start_index=-1, bottom_index=5, end_index=10,
            start_angle=180.0, bottom_angle=90.0, end_angle=180.0,
        )


def test_rep_boundaries_keyed_by_angle_name():
    boundaries = RepBoundaries(
        by_angle={
            "left_knee_flexion": [
                RepBoundaryModel(
                    start_index=0, bottom_index=14, end_index=29,
                    start_angle=180.0, bottom_angle=90.0, end_angle=180.0,
                )
            ]
        }
    )
    assert len(boundaries.by_angle["left_knee_flexion"]) == 1


def test_per_rep_metrics_and_rep_metric():
    metrics = PerRepMetrics(
        primary_angle="left_knee_flexion",
        reps=[
            RepMetric(
                rep_index=0,
                amplitude_deg=90.0,
                peak_velocity_deg_per_s=240.0,
                rom_deg=90.0,
                mean_trunk_lean_deg=4.5,
                mean_knee_valgus_deg=3.1,
            )
        ],
    )
    assert metrics.primary_angle == "left_knee_flexion"
    assert metrics.reps[0].amplitude_deg == 90.0


def test_within_movement_trend_fatigue_flag():
    trend = WithinMovementTrend(
        rom_slope_deg_per_rep=-3.0,
        velocity_slope_deg_per_s_per_rep=-12.0,
        valgus_slope_deg_per_rep=1.5,
        trunk_lean_slope_deg_per_rep=0.5,
        fatigue_detected=True,
    )
    assert trend.fatigue_detected is True


def test_pipeline_artifacts_only_quality_report_required():
    bundle = PipelineArtifacts(
        quality_report=SessionQualityReport(passed=False, issues=[], metrics={}),
    )
    assert bundle.quality_report.passed is False
    assert bundle.angle_series is None
    assert bundle.within_movement_trend is None
