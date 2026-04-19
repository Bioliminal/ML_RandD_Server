from bioliminal.api.schemas import Session
from bioliminal.pipeline.artifacts import PipelineArtifacts
from bioliminal.pipeline.errors import PipelineError, QualityGateError, StageError
from bioliminal.pipeline.registry import StageRegistry
from bioliminal.pipeline.stages.angle_series import run_angle_series
from bioliminal.pipeline.stages.base import (
    STAGE_NAME_ANGLE_SERIES,
    STAGE_NAME_CHAIN_REASONING,
    STAGE_NAME_LIFT,
    STAGE_NAME_NORMALIZE,
    STAGE_NAME_PER_REP_METRICS,
    STAGE_NAME_PHASE_SEGMENT,
    STAGE_NAME_QUALITY_GATE,
    STAGE_NAME_REP_COMPARISON,
    STAGE_NAME_REP_SEGMENT,
    STAGE_NAME_SKELETON,
    STAGE_NAME_WITHIN_MOVEMENT_TREND,
    Stage,
    StageContext,
)
from bioliminal.pipeline.stages.chain_reasoning import run_chain_reasoning
from bioliminal.pipeline.stages.lift import run_lift
from bioliminal.pipeline.stages.normalize import run_normalize
from bioliminal.pipeline.stages.per_rep_metrics import run_per_rep_metrics
from bioliminal.pipeline.stages.phase_segment import run_phase_segment
from bioliminal.pipeline.stages.quality_gate import run_quality_gate
from bioliminal.pipeline.stages.rep_comparison import run_rep_comparison
from bioliminal.pipeline.stages.rep_segment import run_rep_segment
from bioliminal.pipeline.stages.skeleton import run_skeleton
from bioliminal.pipeline.stages.within_movement_trend import run_within_movement_trend


def _default_stage_list() -> list[Stage]:
    """Rep-based pipeline for knee-flexion movements: overhead_squat, single_leg_squat."""
    return [
        Stage(name=STAGE_NAME_QUALITY_GATE, run=run_quality_gate),
        Stage(name=STAGE_NAME_ANGLE_SERIES, run=run_angle_series),
        Stage(name=STAGE_NAME_NORMALIZE, run=run_normalize),
        Stage(name=STAGE_NAME_LIFT, run=run_lift),
        Stage(name=STAGE_NAME_SKELETON, run=run_skeleton),
        Stage(name=STAGE_NAME_REP_SEGMENT, run=run_rep_segment),
        Stage(name=STAGE_NAME_PER_REP_METRICS, run=run_per_rep_metrics),
        Stage(name=STAGE_NAME_WITHIN_MOVEMENT_TREND, run=run_within_movement_trend),
        Stage(name=STAGE_NAME_REP_COMPARISON, run=run_rep_comparison),
        Stage(name=STAGE_NAME_CHAIN_REASONING, run=run_chain_reasoning),
    ]


def _push_up_stage_list() -> list[Stage]:
    """Push-up pipeline: stops at skeleton. Rep-based stages require
    elbow_flexion angles which are deferred to a follow-on epoch."""
    return [
        Stage(name=STAGE_NAME_QUALITY_GATE, run=run_quality_gate),
        Stage(name=STAGE_NAME_ANGLE_SERIES, run=run_angle_series),
        Stage(name=STAGE_NAME_NORMALIZE, run=run_normalize),
        Stage(name=STAGE_NAME_LIFT, run=run_lift),
        Stage(name=STAGE_NAME_SKELETON, run=run_skeleton),
        Stage(name=STAGE_NAME_CHAIN_REASONING, run=run_chain_reasoning),
    ]


def _rollup_stage_list() -> list[Stage]:
    """Phase-based pipeline: rollup. Uses phase_segment instead of rep_segment."""
    return [
        Stage(name=STAGE_NAME_QUALITY_GATE, run=run_quality_gate),
        Stage(name=STAGE_NAME_ANGLE_SERIES, run=run_angle_series),
        Stage(name=STAGE_NAME_NORMALIZE, run=run_normalize),
        Stage(name=STAGE_NAME_LIFT, run=run_lift),
        Stage(name=STAGE_NAME_SKELETON, run=run_skeleton),
        Stage(name=STAGE_NAME_PHASE_SEGMENT, run=run_phase_segment),
    ]


def _bicep_curl_stage_list() -> list[Stage]:
    """Bicep curl pipeline — full rep-based path now that elbow flexion
    and bicep per-rep metrics are wired (ML_RandD_Server#12 + #18)."""
    return [
        Stage(name=STAGE_NAME_QUALITY_GATE, run=run_quality_gate),
        Stage(name=STAGE_NAME_ANGLE_SERIES, run=run_angle_series),
        Stage(name=STAGE_NAME_NORMALIZE, run=run_normalize),
        Stage(name=STAGE_NAME_LIFT, run=run_lift),
        Stage(name=STAGE_NAME_SKELETON, run=run_skeleton),
        Stage(name=STAGE_NAME_REP_SEGMENT, run=run_rep_segment),
        Stage(name=STAGE_NAME_PER_REP_METRICS, run=run_per_rep_metrics),
        Stage(name=STAGE_NAME_CHAIN_REASONING, run=run_chain_reasoning),
    ]


def _build_default_registry() -> StageRegistry:
    registry = StageRegistry()
    registry.register_movement("overhead_squat", _default_stage_list())
    registry.register_movement("single_leg_squat", _default_stage_list())
    registry.register_movement("push_up", _push_up_stage_list())
    registry.register_movement("rollup", _rollup_stage_list())
    registry.register_movement("bicep_curl", _bicep_curl_stage_list())
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
        lift_result=ctx.artifacts.get(STAGE_NAME_LIFT),
        skeleton_result=ctx.artifacts.get(STAGE_NAME_SKELETON),
        phase_boundaries=ctx.artifacts.get(STAGE_NAME_PHASE_SEGMENT),
        chain_observations=ctx.artifacts.get(STAGE_NAME_CHAIN_REASONING),
        movement_temporal_summary=ctx.artifacts.get(STAGE_NAME_REP_COMPARISON),
    )
