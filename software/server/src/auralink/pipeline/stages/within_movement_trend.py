import numpy as np

from auralink.pipeline.artifacts import PerRepMetrics, WithinMovementTrend
from auralink.pipeline.stages.base import StageContext

FATIGUE_ROM_SLOPE_THRESHOLD = -2.0
FATIGUE_VALGUS_SLOPE_THRESHOLD = 1.0
FATIGUE_TRUNK_LEAN_SLOPE_THRESHOLD = 1.0


def _slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    xs = np.arange(len(values), dtype=np.float64)
    ys = np.asarray(values, dtype=np.float64)
    slope, _intercept = np.polyfit(xs, ys, 1)
    return float(slope)


def run_within_movement_trend(ctx: StageContext) -> WithinMovementTrend:
    metrics: PerRepMetrics = ctx.artifacts["per_rep_metrics"]
    reps = metrics.reps
    rom_slope = _slope([r.rom_deg for r in reps])
    vel_slope = _slope([r.peak_velocity_deg_per_s for r in reps])
    valgus_slope = _slope([r.mean_knee_valgus_deg for r in reps])
    trunk_slope = _slope([r.mean_trunk_lean_deg for r in reps])

    fatigue = (
        rom_slope <= FATIGUE_ROM_SLOPE_THRESHOLD
        or valgus_slope >= FATIGUE_VALGUS_SLOPE_THRESHOLD
        or trunk_slope >= FATIGUE_TRUNK_LEAN_SLOPE_THRESHOLD
    )

    return WithinMovementTrend(
        rom_slope_deg_per_rep=rom_slope,
        velocity_slope_deg_per_s_per_rep=vel_slope,
        valgus_slope_deg_per_rep=valgus_slope,
        trunk_lean_slope_deg_per_rep=trunk_slope,
        fatigue_detected=fatigue,
    )
