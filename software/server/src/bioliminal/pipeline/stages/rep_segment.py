from bioliminal.analysis.rep_segmentation import segment_reps
from bioliminal.api.schemas import MovementType
from bioliminal.pipeline.artifacts import NormalizedAngleTimeSeries, RepBoundaries, RepBoundaryModel
from bioliminal.pipeline.stages.base import StageContext

PRIMARY_REP_ANGLES_BY_MOVEMENT: dict[MovementType, tuple[str, ...]] = {
    "overhead_squat": ("left_knee_flexion", "right_knee_flexion"),
    "single_leg_squat": ("left_knee_flexion", "right_knee_flexion"),
    "bicep_curl": ("left_elbow_flexion", "right_elbow_flexion"),
}

MIN_AMPLITUDE_DEG = 30.0
# A boundary shared between two adjacent reps is classified as a jitter-split
# if the boundary angle is in the lower fraction of the movement's full range.
# Below 0.5 → bottom half → likely a spurious mid-rep spike, merge.
_JITTER_BOUNDARY_FRACTION = 0.5


def _merge_jitter_splits(raw_reps: list, series: list[float]) -> list[RepBoundaryModel]:
    """Merge adjacent reps whose shared boundary is near the movement bottom.

    When a mid-rep jitter spike creates a spurious local max, ``segment_reps``
    emits two half-reps joined at the spike.  The spike sits near the bottom
    of the movement (low angle), so end_angle of the first half is low.
    Genuine rep boundaries (extension peak) have high end_angle.
    """
    if not raw_reps:
        return []

    series_min = min(series)
    series_max = max(series)
    series_range = series_max - series_min or 1.0

    result: list[RepBoundaryModel] = []
    i = 0
    while i < len(raw_reps):
        rep = raw_reps[i]
        # Merge forward while the shared boundary is near the bottom.
        while i + 1 < len(raw_reps):
            nxt = raw_reps[i + 1]
            if nxt.start_index != rep.end_index:
                break
            boundary_fraction = (rep.end_angle - series_min) / series_range
            if boundary_fraction >= _JITTER_BOUNDARY_FRACTION:
                break  # Genuine extension peak — do not merge.
            bottom_idx = (
                rep.bottom_index
                if series[rep.bottom_index] <= series[nxt.bottom_index]
                else nxt.bottom_index
            )
            rep = type(rep)(
                start_index=rep.start_index,
                bottom_index=bottom_idx,
                end_index=nxt.end_index,
                start_angle=rep.start_angle,
                bottom_angle=series[bottom_idx],
                end_angle=nxt.end_angle,
            )
            i += 1
        result.append(
            RepBoundaryModel(
                start_index=rep.start_index,
                bottom_index=rep.bottom_index,
                end_index=rep.end_index,
                start_angle=rep.start_angle,
                bottom_angle=rep.bottom_angle,
                end_angle=rep.end_angle,
            )
        )
        i += 1
    return result


def run_rep_segment(ctx: StageContext) -> RepBoundaries:
    normalized: NormalizedAngleTimeSeries = ctx.artifacts["normalize"]
    primary = PRIMARY_REP_ANGLES_BY_MOVEMENT.get(ctx.movement_type, ())
    by_angle: dict[str, list[RepBoundaryModel]] = {}
    for angle_name in primary:
        series = normalized.angles.get(angle_name, [])
        raw_reps = segment_reps(series, min_amplitude=MIN_AMPLITUDE_DEG)
        by_angle[angle_name] = _merge_jitter_splits(raw_reps, list(series))
    return RepBoundaries(by_angle=by_angle)
