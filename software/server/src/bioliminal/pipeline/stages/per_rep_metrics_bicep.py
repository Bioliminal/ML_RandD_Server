"""Bicep-specific per-rep metric computation.

Called from per_rep_metrics.run_per_rep_metrics when ctx.movement_type == 'bicep_curl'.
See research/synthesis/bicep-curl-server-thresholds-2026-04-19.md §C for formula sources.
"""
import numpy as np
from scipy.signal import savgol_filter

from bioliminal.pipeline.artifacts import (
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    RepBoundaries,
    RepMetric,
)
from bioliminal.pipeline.stages.base import StageContext

PRIMARY_ANGLE = "left_elbow_flexion"

_SG_WINDOW = 5
_SG_ORDER = 2


def _peak_velocity_deg_per_s(window: list[float], frame_rate: float) -> float:
    """Central-difference derivative smoothed with Savitzky-Golay; take max absolute."""
    if len(window) < _SG_WINDOW:
        if len(window) < 2:
            return 0.0
        deltas = np.abs(np.diff(np.asarray(window, dtype=np.float64)))
        return float(np.max(deltas) * frame_rate)
    smoothed = savgol_filter(
        np.asarray(window, dtype=np.float64),
        window_length=_SG_WINDOW,
        polyorder=_SG_ORDER,
        deriv=1,
    )
    return float(np.max(np.abs(smoothed)) * frame_rate)


def _cv_pct(values: list[float]) -> float:
    if not values:
        return 0.0
    arr = np.asarray(values, dtype=np.float64)
    mean = float(np.mean(arr))
    if mean == 0.0:
        return 0.0
    return float(np.std(arr, ddof=0) / mean * 100.0)


def _decline_pct(values: list[float]) -> float:
    """Peak-velocity decline from first rep to last, as a fraction in [0, 1]."""
    if len(values) < 2:
        return 0.0
    first = values[0]
    last = values[-1]
    if first <= 0.0:
        return 0.0
    return float(max(0.0, (first - last) / first))


def run_bicep_per_rep_metrics(ctx: StageContext) -> PerRepMetrics:
    normalized: NormalizedAngleTimeSeries = ctx.artifacts["normalize"]
    reps: RepBoundaries = ctx.artifacts["rep_segment"]
    frame_rate = ctx.session.metadata.frame_rate

    elbow = normalized.angles.get(PRIMARY_ANGLE, [])
    boundaries = reps.by_angle.get(PRIMARY_ANGLE, [])

    amplitudes: list[float] = []
    concentric_times: list[float] = []
    eccentric_times: list[float] = []
    peak_velocities: list[float] = []
    roms: list[float] = []

    for rep in boundaries:
        window = elbow[rep.start_index : rep.end_index + 1]
        rom = float(max(window) - min(window)) if window else 0.0
        amplitude = float(max(rep.start_angle, rep.end_angle) - rep.bottom_angle)
        concentric_s = (rep.bottom_index - rep.start_index) / frame_rate if frame_rate > 0 else 0.0
        eccentric_s = (rep.end_index - rep.bottom_index) / frame_rate if frame_rate > 0 else 0.0
        peak_v = _peak_velocity_deg_per_s(window, frame_rate)

        amplitudes.append(amplitude)
        concentric_times.append(concentric_s)
        eccentric_times.append(eccentric_s)
        peak_velocities.append(peak_v)
        roms.append(rom)

    velocity_decline = _decline_pct(peak_velocities)
    amplitude_cv = _cv_pct(amplitudes)
    tempo_cv = _cv_pct(concentric_times)

    out: list[RepMetric] = []
    for idx, rep in enumerate(boundaries):
        out.append(RepMetric(
            rep_index=idx,
            amplitude_deg=amplitudes[idx],
            peak_velocity_deg_per_s=peak_velocities[idx],
            rom_deg=roms[idx],
            mean_trunk_lean_deg=0.0,
            mean_knee_valgus_deg=0.0,
            concentric_s=concentric_times[idx],
            eccentric_s=eccentric_times[idx],
            velocity_decline_pct=velocity_decline,
            amplitude_cv_pct=amplitude_cv,
            tempo_cv_pct=tempo_cv,
        ))
    return PerRepMetrics(primary_angle=PRIMARY_ANGLE, reps=out)
