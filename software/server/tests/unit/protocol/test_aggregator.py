from bioliminal.pipeline.artifacts import (
    MovementTemporalSummary,
    SessionQualityReport,
)
from bioliminal.protocol.aggregator import aggregate_protocol
from bioliminal.report.schemas import MovementSection, Report, ReportMetadata


def _movement_section(movement: str, summary: MovementTemporalSummary | None) -> MovementSection:
    return MovementSection(
        movement=movement,
        quality_report=SessionQualityReport(passed=True, issues=[], metrics={}),
        movement_temporal_summary=summary,
    )


def _mk_report(session_id: str, movement: str, mean_ncc: float, mean_rom_dev: float) -> Report:
    summary = MovementTemporalSummary(
        primary_angle="left_knee_flexion",
        rep_comparisons=[],
        mean_ncc=mean_ncc,
        ncc_slope_per_rep=0.0,
        mean_rom_deviation_pct=mean_rom_dev,
        form_drift_detected=False,
    )
    return Report(
        metadata=ReportMetadata(session_id=session_id, movement=movement),
        movement_section=_movement_section(movement, summary),
        overall_narrative="stub",
    )


def test_single_session_aggregates_trivially():
    reports = [_mk_report("s1", "overhead_squat", 0.95, -2.0)]
    protocol = aggregate_protocol(reports, ["s1"])
    assert protocol.session_ids == ["s1"]
    assert protocol.per_session_movements == {"s1": "overhead_squat"}
    assert protocol.fatigue_carryover_detected is False


def test_two_sessions_stable_no_carryover():
    reports = [
        _mk_report("s1", "overhead_squat", 0.95, -2.0),
        _mk_report("s2", "single_leg_squat", 0.95, -3.0),
    ]
    protocol = aggregate_protocol(reports, ["s1", "s2"])
    assert protocol.fatigue_carryover_detected is False


def test_four_sessions_declining_ncc_and_growing_rom_triggers_carryover():
    reports = [
        _mk_report("s1", "overhead_squat", 0.97, -2.0),
        _mk_report("s2", "single_leg_squat", 0.92, -8.0),
        _mk_report("s3", "push_up", 0.88, -14.0),
        _mk_report("s4", "rollup", 0.82, -20.0),
    ]
    protocol = aggregate_protocol(reports, ["s1", "s2", "s3", "s4"])
    assert protocol.fatigue_carryover_detected is True
    ncc_metric = next(m for m in protocol.cross_movement_metrics if m.metric_name == "mean_ncc")
    assert ncc_metric.trend == "declining"


def test_session_without_movement_temporal_summary_is_skipped():
    reports = [
        _mk_report("s1", "overhead_squat", 0.95, -2.0),
        # session with no temporal summary attached — real constructor, summary=None
    ]
    bare_report = Report(
        metadata=ReportMetadata(session_id="s2", movement="push_up"),
        movement_section=_movement_section("push_up", summary=None),
        overall_narrative="stub",
    )
    reports.append(bare_report)
    protocol = aggregate_protocol(reports, ["s1", "s2"])
    assert "s2" in protocol.per_session_movements
    assert protocol.per_session_movements["s2"] == "push_up"
    ncc_metric = next(
        (m for m in protocol.cross_movement_metrics if m.metric_name == "mean_ncc"),
        None,
    )
    assert ncc_metric is not None
    assert "s1" in ncc_metric.values_by_session
    assert "s2" not in ncc_metric.values_by_session


def test_repeated_same_movement_sessions_do_not_overwrite_each_other():
    """Regression guard: before the session_id keying fix, four overhead_squat
    sessions collapsed into a single entry, breaking cross-session metrics.
    """
    reports = [
        _mk_report("s1", "overhead_squat", 0.97, -2.0),
        _mk_report("s2", "overhead_squat", 0.93, -6.0),
        _mk_report("s3", "overhead_squat", 0.89, -12.0),
        _mk_report("s4", "overhead_squat", 0.85, -18.0),
    ]
    protocol = aggregate_protocol(reports, ["s1", "s2", "s3", "s4"])
    ncc_metric = next(m for m in protocol.cross_movement_metrics if m.metric_name == "mean_ncc")
    assert set(ncc_metric.values_by_session.keys()) == {"s1", "s2", "s3", "s4"}
    assert ncc_metric.values_by_session["s1"] == 0.97
    assert ncc_metric.values_by_session["s4"] == 0.85
