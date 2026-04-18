"""Within-movement aggregation over a list of RepComparisons.

Produces a MovementTemporalSummary with the mean NCC, the linear-fit slope
of NCC across reps (same polyfit idiom used by within_movement_trend), and
a form_drift_detected flag that fires on the JOINT condition of negative NCC
slope AND large mean ROM deviation. Joint (not either-or) to avoid false
positives from a single noisy rep or a consistent but shape-matched
lower-ROM set.
"""

import math

import numpy as np

from bioliminal.pipeline.artifacts import MovementTemporalSummary, RepComparison
from bioliminal.temporal.threshold_loader import TemporalThresholds


def _slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    xs = np.arange(len(values), dtype=np.float64)
    ys = np.asarray(values, dtype=np.float64)
    slope, _intercept = np.polyfit(xs, ys, 1)
    return float(slope)


def _finite_ncc_scores(comparisons: list[RepComparison]) -> list[float]:
    return [c.ncc_score for c in comparisons if not math.isnan(c.ncc_score)]


def summarize_comparisons(
    comparisons: list[RepComparison],
    primary_angle: str,
    thresholds: TemporalThresholds,
) -> MovementTemporalSummary:
    """Aggregate per-rep comparisons into a within-movement summary.

    NaN NCC scores (empty reps) are excluded from mean/slope computation so
    one dropout does not drag the aggregate. rom_deviation_pct is used as-is
    (there is no defined NaN state for it).
    """
    finite_ncc = _finite_ncc_scores(comparisons)
    mean_ncc = float(np.mean(finite_ncc)) if finite_ncc else float("nan")
    ncc_slope = _slope(finite_ncc)

    rom_dev_values = [c.rom_deviation_pct for c in comparisons]
    mean_rom_dev = float(np.mean(rom_dev_values)) if rom_dev_values else 0.0

    drift = (
        ncc_slope <= thresholds.form_drift_ncc_slope_threshold
        and abs(mean_rom_dev) >= thresholds.form_drift_rom_mean_deviation_pct
    )

    return MovementTemporalSummary(
        primary_angle=primary_angle,
        rep_comparisons=comparisons,
        mean_ncc=mean_ncc if not math.isnan(mean_ncc) else 0.0,
        ncc_slope_per_rep=ncc_slope,
        mean_rom_deviation_pct=mean_rom_dev,
        form_drift_detected=drift,
    )
