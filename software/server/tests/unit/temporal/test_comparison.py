import math

import pytest

from bioliminal.temporal.comparison import compare_rep
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


def _cosine_rep(n: int = 30, amplitude: float = 45.0, offset: float = 135.0) -> list[float]:
    return [offset + amplitude * math.cos(2.0 * math.pi * i / n) for i in range(n)]


def test_identical_rep_is_clean(thresholds):
    ref = _cosine_rep()
    user = list(ref)
    result = compare_rep(user, ref, "left_knee_flexion", 0, thresholds)
    assert result.status == "clean"
    assert result.ncc_score == pytest.approx(1.0, abs=1e-9)
    assert abs(result.rom_deviation_pct) < 0.5


def test_half_rom_rep_is_flagged_despite_matching_shape(thresholds):
    """NCC amplitude guard — a half-range rep has ncc ~1.0 but must flag.

    DTW is amplitude-sensitive so the warp path diverges slightly for scaled
    signals, yielding NCC ~0.97 rather than exactly 1.0. The critical
    assertion is that status=="flag" via the ROM guard, not the NCC value.
    """
    ref = _cosine_rep(amplitude=45.0)
    user = _cosine_rep(amplitude=22.5)  # same shape, half ROM
    result = compare_rep(user, ref, "left_knee_flexion", 1, thresholds)
    assert result.ncc_score == pytest.approx(1.0, abs=0.05)  # ~1.0, not exact
    assert result.status == "flag"
    assert result.rom_deviation_pct < -40.0  # roughly -50%


def test_slight_rom_drop_with_matching_shape_is_concern(thresholds):
    ref = _cosine_rep(amplitude=45.0)
    user = _cosine_rep(amplitude=36.0)  # -20% ROM -> concern band
    result = compare_rep(user, ref, "left_knee_flexion", 2, thresholds)
    assert result.ncc_score == pytest.approx(1.0, abs=0.05)  # ~1.0, not exact
    assert result.status == "concern"
    assert -25.0 < result.rom_deviation_pct < -15.0


def test_inverse_rep_is_flagged(thresholds):
    ref = _cosine_rep()
    user = [180.0 - v for v in ref]  # shape-inverted
    result = compare_rep(user, ref, "left_knee_flexion", 3, thresholds)
    # status flag from NCC branch (ncc will be -1 or close to it)
    assert result.status == "flag"


def test_empty_user_rep_is_flagged(thresholds):
    ref = _cosine_rep()
    result = compare_rep([], ref, "left_knee_flexion", 4, thresholds)
    assert result.status == "flag"
    assert math.isnan(result.ncc_score)
