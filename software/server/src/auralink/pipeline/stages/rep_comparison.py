"""rep_comparison pipeline stage.

Consumes:
  - ctx.artifacts["per_rep_metrics"]  (PerRepMetrics, from Plan 1)
  - ctx.artifacts["rep_segment"]      (RepBoundaries, from Plan 1)
  - ctx.artifacts["normalize"]        (NormalizedAngleTimeSeries, from Plan 1)

Produces:
  - MovementTemporalSummary

Runs only on movements that have per_rep_metrics — i.e., overhead_squat and
single_leg_squat. push_up and rollup never hit this stage because they are
not wired into the orchestrator lists for those movements.
"""

from auralink.pipeline.artifacts import (
    MovementTemporalSummary,
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    RepBoundaries,
    RepComparison,
)
from auralink.pipeline.stages.base import StageContext
from auralink.temporal.comparison import compare_rep
from auralink.temporal.reference_reps import load_reference_rep
from auralink.temporal.summary import summarize_comparisons
from auralink.temporal.threshold_loader import load_temporal_thresholds


def run_rep_comparison(ctx: StageContext) -> MovementTemporalSummary:
    metrics: PerRepMetrics = ctx.artifacts["per_rep_metrics"]
    normalized: NormalizedAngleTimeSeries = ctx.artifacts["normalize"]
    rep_boundaries: RepBoundaries = ctx.artifacts["rep_segment"]

    primary_angle = metrics.primary_angle
    movement = ctx.session.metadata.movement

    reference = load_reference_rep(movement)
    if primary_angle not in reference.angles:
        raise KeyError(
            f"reference rep for {movement} has no angle {primary_angle!r}; "
            f"available: {sorted(reference.angles.keys())}"
        )
    reference_angles = reference.angles[primary_angle]

    thresholds = load_temporal_thresholds()
    user_trace = normalized.angles.get(primary_angle, [])
    boundaries = rep_boundaries.by_angle.get(primary_angle, [])

    comparisons: list[RepComparison] = []
    for idx, rep in enumerate(boundaries):
        window = user_trace[rep.start_index : rep.end_index + 1]
        comparisons.append(
            compare_rep(
                user_angles=window,
                reference_angles=reference_angles,
                angle_name=primary_angle,
                rep_index=idx,
                thresholds=thresholds,
            )
        )

    return summarize_comparisons(
        comparisons=comparisons,
        primary_angle=primary_angle,
        thresholds=thresholds,
    )
