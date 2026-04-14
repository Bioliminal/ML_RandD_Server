"""Per-rep comparison against a reference rep.

Pipeline: DTW align (run_dtw) -> re-index via warping path -> NCC score
(ncc) -> ROM deviation -> joint clean/concern/flag status.

The status classification enforces the NCC amplitude guard (see
docs/plans/2026-04-10-L2-3-dtw-temporal.md architectural decision 5): NCC
alone is scale-invariant and will score a half-range rep near 1.0, so ROM
deviation is checked independently and the worst of the two classifications
wins.
"""

import math

import numpy as np

from auralink.pipeline.artifacts import RepComparison
from auralink.temporal.dtw import run_dtw
from auralink.temporal.ncc import ncc
from auralink.temporal.threshold_loader import TemporalThresholds

_STATUS_ORDER = {"clean": 0, "concern": 1, "flag": 2}
_INVERSE_ORDER = {v: k for k, v in _STATUS_ORDER.items()}


def _rom(window: list[float]) -> float:
    if not window:
        return 0.0
    return float(max(window) - min(window))


def _classify_ncc(score: float, thresholds: TemporalThresholds) -> str:
    if math.isnan(score):
        return "flag"
    if score >= thresholds.ncc_clean_min:
        return "clean"
    if score >= thresholds.ncc_concern_min:
        return "concern"
    return "flag"


def _classify_rom(deviation_pct: float, thresholds: TemporalThresholds) -> str:
    abs_dev = abs(deviation_pct)
    if abs_dev >= thresholds.rom_deviation_flag_pct:
        return "flag"
    if abs_dev >= thresholds.rom_deviation_concern_pct:
        return "concern"
    return "clean"


def _worst(a: str, b: str) -> str:
    return _INVERSE_ORDER[max(_STATUS_ORDER[a], _STATUS_ORDER[b])]


def compare_rep(
    user_angles: list[float],
    reference_angles: list[float],
    angle_name: str,
    rep_index: int,
    thresholds: TemporalThresholds,
) -> RepComparison:
    """Compare one user rep against the reference rep for a single angle.

    Handles empty windows by returning a `flag` status with a NaN NCC score
    rather than raising — empty reps are usually an upstream rep-segment
    issue and should surface as data quality flags, not pipeline crashes.
    """
    if not user_angles or not reference_angles:
        return RepComparison(
            rep_index=rep_index,
            angle=angle_name,
            ncc_score=float("nan"),
            dtw_distance=0.0,
            rom_user_deg=_rom(user_angles),
            rom_reference_deg=_rom(reference_angles),
            rom_deviation_pct=0.0,
            status="flag",
        )

    dtw_result = run_dtw(user_angles, reference_angles)
    # Re-index both sequences along the warp path so they become equal-length
    # for zero-lag NCC. The warp path is a list of (i_user, j_ref) tuples.
    user_aligned = np.array([user_angles[i] for i, _ in dtw_result.path], dtype=np.float64)
    ref_aligned = np.array([reference_angles[j] for _, j in dtw_result.path], dtype=np.float64)
    ncc_score = ncc(user_aligned, ref_aligned)

    rom_user = _rom(user_angles)
    rom_ref = _rom(reference_angles)
    rom_deviation_pct = (rom_user - rom_ref) / rom_ref * 100.0 if rom_ref > 0.0 else 0.0

    ncc_status = _classify_ncc(ncc_score, thresholds)
    rom_status = _classify_rom(rom_deviation_pct, thresholds)
    status = _worst(ncc_status, rom_status)

    return RepComparison(
        rep_index=rep_index,
        angle=angle_name,
        ncc_score=float(ncc_score) if not math.isnan(ncc_score) else float("nan"),
        dtw_distance=dtw_result.distance,
        rom_user_deg=rom_user,
        rom_reference_deg=rom_ref,
        rom_deviation_pct=rom_deviation_pct,
        status=status,  # type: ignore[arg-type]
    )
