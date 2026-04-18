import pytest

from bioliminal.pipeline.artifacts import RepComparison
from bioliminal.temporal.summary import summarize_comparisons
from bioliminal.temporal.threshold_loader import TemporalThresholds


@pytest.fixture
def thresholds() -> TemporalThresholds:
    return TemporalThresholds(
        ncc_clean_min=0.95,
        ncc_concern_min=0.75,
        rom_deviation_concern_pct=15.0,
        rom_deviation_flag_pct=25.0,
        form_drift_ncc_slope_threshold=-0.02,
        form_drift_rom_mean_deviation_pct=15.0,
    )


def _mk(rep_index: int, ncc: float, rom_dev_pct: float) -> RepComparison:
    return RepComparison(
        rep_index=rep_index,
        angle="left_knee_flexion",
        ncc_score=ncc,
        dtw_distance=1.0,
        rom_user_deg=90.0 * (1.0 + rom_dev_pct / 100.0),
        rom_reference_deg=90.0,
        rom_deviation_pct=rom_dev_pct,
        status="clean",
    )


def test_flat_ncc_no_drift(thresholds):
    comparisons = [_mk(i, 0.97, -2.0) for i in range(5)]
    summary = summarize_comparisons(comparisons, "left_knee_flexion", thresholds)
    assert summary.form_drift_detected is False
    assert summary.mean_ncc == pytest.approx(0.97, abs=1e-9)
    assert abs(summary.ncc_slope_per_rep) < 1e-9


def test_ncc_decline_alone_without_rom_deviation_does_not_trigger_drift(thresholds):
    # NCC clearly declining, but ROM deviation stays small -> no drift by
    # the joint-condition rule.
    comparisons = [_mk(i, 0.98 - 0.05 * i, -1.0) for i in range(5)]
    summary = summarize_comparisons(comparisons, "left_knee_flexion", thresholds)
    assert summary.ncc_slope_per_rep <= -0.02
    assert summary.form_drift_detected is False


def test_rom_deviation_alone_without_ncc_decline_does_not_trigger_drift(thresholds):
    comparisons = [_mk(i, 0.97, -20.0) for i in range(5)]
    summary = summarize_comparisons(comparisons, "left_knee_flexion", thresholds)
    assert abs(summary.mean_rom_deviation_pct) >= 15.0
    assert summary.form_drift_detected is False


def test_combined_ncc_decline_and_rom_deviation_triggers_drift(thresholds):
    comparisons = [_mk(i, 0.98 - 0.05 * i, -18.0) for i in range(5)]
    summary = summarize_comparisons(comparisons, "left_knee_flexion", thresholds)
    assert summary.form_drift_detected is True
