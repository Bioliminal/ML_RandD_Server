from auralink.analysis.rep_segmentation import segment_reps
from auralink.api.schemas import MovementType
from auralink.pipeline.artifacts import NormalizedAngleTimeSeries, RepBoundaries, RepBoundaryModel
from auralink.pipeline.stages.base import StageContext

PRIMARY_REP_ANGLES_BY_MOVEMENT: dict[MovementType, tuple[str, ...]] = {
    "overhead_squat": ("left_knee_flexion", "right_knee_flexion"),
    "single_leg_squat": ("left_knee_flexion", "right_knee_flexion"),
}

MIN_AMPLITUDE_DEG = 30.0


def run_rep_segment(ctx: StageContext) -> RepBoundaries:
    normalized: NormalizedAngleTimeSeries = ctx.artifacts["normalize"]
    primary = PRIMARY_REP_ANGLES_BY_MOVEMENT.get(ctx.movement_type, ())
    by_angle: dict[str, list[RepBoundaryModel]] = {}
    for angle_name in primary:
        series = normalized.angles.get(angle_name, [])
        raw_reps = segment_reps(series, min_amplitude=MIN_AMPLITUDE_DEG)
        by_angle[angle_name] = [
            RepBoundaryModel(
                start_index=rep.start_index,
                bottom_index=rep.bottom_index,
                end_index=rep.end_index,
                start_angle=rep.start_angle,
                bottom_angle=rep.bottom_angle,
                end_angle=rep.end_angle,
            )
            for rep in raw_reps
        ]
    return RepBoundaries(by_angle=by_angle)
