from auralink.pipeline.stages.base import (
    STAGE_NAME_PER_REP_METRICS,
    StageContext,
)
from auralink.reasoning.observations import ChainObservation
from auralink.reasoning.rule_engine import ChainReasoner, RuleBasedChainReasoner
from auralink.reasoning.rule_loader import load_rules
from auralink.reasoning.threshold_loader import (
    load_body_type_adjustments,
    load_default_thresholds,
)


def _build_default_reasoner() -> RuleBasedChainReasoner:
    return RuleBasedChainReasoner(
        rules=load_rules(),
        base_thresholds=load_default_thresholds(),
        adjustments=load_body_type_adjustments(),
    )


_default_reasoner: ChainReasoner = _build_default_reasoner()


def run_chain_reasoning(
    ctx: StageContext,
    reasoner: ChainReasoner | None = None,
) -> list[ChainObservation]:
    """Apply rule-based chain reasoning over per-rep metrics.

    Reads PerRepMetrics from the prior stage and returns a list of
    ChainObservations. Returns an empty list if per_rep_metrics is missing
    (push_up stops at skeleton; rollup uses phase_segment instead of reps).
    """
    impl = reasoner if reasoner is not None else _default_reasoner
    per_rep = ctx.artifacts.get(STAGE_NAME_PER_REP_METRICS)
    return impl.reason(
        per_rep,
        ctx.session.metadata.movement,
        body_type=None,
    )
