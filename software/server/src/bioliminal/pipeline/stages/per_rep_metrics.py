import numpy as np

from bioliminal.pipeline.artifacts import (
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    RepBoundaries,
    RepMetric,
)
from bioliminal.pipeline.stages.base import StageContext

PRIMARY_ANGLE = "left_knee_flexion"


def _slice(series: list[float], start: int, end: int) -> list[float]:
    return series[start : end + 1]


def run_per_rep_metrics(ctx: StageContext) -> PerRepMetrics:
    normalized: NormalizedAngleTimeSeries = ctx.artifacts["normalize"]
    reps: RepBoundaries = ctx.artifacts["rep_segment"]
    frame_rate = ctx.session.metadata.frame_rate
    boundaries = reps.by_angle.get(PRIMARY_ANGLE, [])

    knee = normalized.angles.get(PRIMARY_ANGLE, [])
    trunk = normalized.angles.get("trunk_lean", [])
    valgus_l = normalized.angles.get("left_knee_valgus", [])
    valgus_r = normalized.angles.get("right_knee_valgus", [])

    out: list[RepMetric] = []
    for idx, rep in enumerate(boundaries):
        window = _slice(knee, rep.start_index, rep.end_index)
        rom = float(max(window) - min(window)) if window else 0.0
        amplitude = float(max(rep.start_angle, rep.end_angle) - rep.bottom_angle)

        if len(window) >= 2:
            deltas = np.abs(np.diff(np.asarray(window, dtype=np.float64)))
            peak_velocity = float(np.max(deltas) * frame_rate)
        else:
            peak_velocity = 0.0

        trunk_window = _slice(trunk, rep.start_index, rep.end_index) or [0.0]
        valgus_left_window = _slice(valgus_l, rep.start_index, rep.end_index) or [0.0]
        valgus_right_window = _slice(valgus_r, rep.start_index, rep.end_index) or [0.0]
        mean_trunk = float(np.mean(trunk_window))
        per_frame_max_valgus = [
            max(a, b) for a, b in zip(valgus_left_window, valgus_right_window, strict=False)
        ]
        mean_valgus = float(np.mean(per_frame_max_valgus)) if per_frame_max_valgus else 0.0

        out.append(
            RepMetric(
                rep_index=idx,
                amplitude_deg=amplitude,
                peak_velocity_deg_per_s=peak_velocity,
                rom_deg=rom,
                mean_trunk_lean_deg=mean_trunk,
                mean_knee_valgus_deg=mean_valgus,
            )
        )

    return PerRepMetrics(primary_angle=PRIMARY_ANGLE, reps=out)
