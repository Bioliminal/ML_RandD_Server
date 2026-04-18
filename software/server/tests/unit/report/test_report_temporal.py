from bioliminal.pipeline.artifacts import (
    MovementTemporalSummary,
    PipelineArtifacts,
    RepComparison,
    SessionQualityReport,
)
from bioliminal.protocol.schemas import CrossMovementMetric
from bioliminal.report.assembler import assemble_report
from bioliminal.report.schemas import CrossMovementSection, Report, TemporalSection


def _mk_summary() -> MovementTemporalSummary:
    return MovementTemporalSummary(
        primary_angle="left_knee_flexion",
        rep_comparisons=[
            RepComparison(
                rep_index=0,
                angle="left_knee_flexion",
                ncc_score=0.97,
                dtw_distance=1.2,
                rom_user_deg=88.0,
                rom_reference_deg=90.0,
                rom_deviation_pct=-2.22,
                status="clean",
            )
        ],
        mean_ncc=0.97,
        ncc_slope_per_rep=0.0,
        mean_rom_deviation_pct=-2.22,
        form_drift_detected=False,
    )


def test_temporal_section_holds_movement_temporal_summary():
    section = TemporalSection(movement_temporal_summary=_mk_summary())
    assert section.movement_temporal_summary is not None
    assert section.movement_temporal_summary.primary_angle == "left_knee_flexion"


def test_cross_movement_section_holds_metrics():
    metric = CrossMovementMetric(
        metric_name="mean_ncc",
        values_by_session={"s1": 0.95},
        trend="stable",
    )
    section = CrossMovementSection(cross_movement_metrics=[metric])
    assert len(section.cross_movement_metrics) == 1
    assert section.cross_movement_metrics[0].metric_name == "mean_ncc"


def test_assembler_populates_temporal_section_from_artifacts():
    artifacts = PipelineArtifacts(
        quality_report=SessionQualityReport(passed=True, issues=[], metrics={}),
        movement_temporal_summary=_mk_summary(),
    )
    report: Report = assemble_report(
        artifacts=artifacts,
        session_id="sid",
        movement="overhead_squat",
    )
    assert report.temporal_section is not None
    assert report.temporal_section.movement_temporal_summary is not None
    assert report.temporal_section.movement_temporal_summary.mean_ncc == 0.97
    assert report.cross_movement_section is None
    assert report.movement_section.movement_temporal_summary is not None
