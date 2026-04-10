from auralink.api.schemas import Session
from auralink.pipeline.artifacts import PipelineArtifacts
from auralink.pipeline.errors import PipelineError, QualityGateError, StageError
from auralink.pipeline.registry import StageRegistry
from auralink.pipeline.stages.angle_series import run_angle_series
from auralink.pipeline.stages.base import (
    STAGE_NAME_ANGLE_SERIES,
    STAGE_NAME_NORMALIZE,
    STAGE_NAME_PER_REP_METRICS,
    STAGE_NAME_QUALITY_GATE,
    STAGE_NAME_REP_SEGMENT,
    STAGE_NAME_WITHIN_MOVEMENT_TREND,
    Stage,
    StageContext,
)
from auralink.pipeline.stages.normalize import run_normalize
from auralink.pipeline.stages.per_rep_metrics import run_per_rep_metrics
from auralink.pipeline.stages.quality_gate import run_quality_gate
from auralink.pipeline.stages.rep_segment import run_rep_segment
from auralink.pipeline.stages.within_movement_trend import run_within_movement_trend


def _default_stage_list() -> list[Stage]:
    return [
        Stage(name=STAGE_NAME_QUALITY_GATE, run=run_quality_gate),
        Stage(name=STAGE_NAME_ANGLE_SERIES, run=run_angle_series),
        Stage(name=STAGE_NAME_NORMALIZE, run=run_normalize),
        Stage(name=STAGE_NAME_REP_SEGMENT, run=run_rep_segment),
        Stage(name=STAGE_NAME_PER_REP_METRICS, run=run_per_rep_metrics),
        Stage(name=STAGE_NAME_WITHIN_MOVEMENT_TREND, run=run_within_movement_trend),
    ]


def _build_default_registry() -> StageRegistry:
    registry = StageRegistry()
    registry.register_movement("overhead_squat", _default_stage_list())
    registry.register_movement("single_leg_squat", _default_stage_list())
    return registry


DEFAULT_REGISTRY = _build_default_registry()


def run_pipeline(
    session: Session,
    registry: StageRegistry | None = None,
) -> PipelineArtifacts:
    reg = registry if registry is not None else DEFAULT_REGISTRY
    stages = reg.get_stages(session.metadata.movement)

    ctx = StageContext(session=session)
    for stage in stages:
        try:
            result = stage.run(ctx)
        except PipelineError:
            raise
        except Exception as exc:
            raise StageError(stage_name=stage.name, detail=str(exc)) from exc

        ctx.artifacts[stage.name] = result

        if stage.name == STAGE_NAME_QUALITY_GATE and not result.passed:
            raise QualityGateError(report=result)

    return _assemble_artifacts(ctx)


def _assemble_artifacts(ctx: StageContext) -> PipelineArtifacts:
    return PipelineArtifacts(
        quality_report=ctx.artifacts[STAGE_NAME_QUALITY_GATE],
        angle_series=ctx.artifacts.get(STAGE_NAME_ANGLE_SERIES),
        normalized_angle_series=ctx.artifacts.get(STAGE_NAME_NORMALIZE),
        rep_boundaries=ctx.artifacts.get(STAGE_NAME_REP_SEGMENT),
        per_rep_metrics=ctx.artifacts.get(STAGE_NAME_PER_REP_METRICS),
        within_movement_trend=ctx.artifacts.get(STAGE_NAME_WITHIN_MOVEMENT_TREND),
    )
