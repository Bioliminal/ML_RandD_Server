from auralink.pipeline.orchestrator import (
    _default_stage_list,
    _push_up_stage_list,
    _rollup_stage_list,
)
from auralink.pipeline.stages.base import (
    STAGE_NAME_CHAIN_REASONING,
    STAGE_NAME_PER_REP_METRICS,
    STAGE_NAME_REP_COMPARISON,
)


def test_rep_comparison_constant_exists_and_is_unique():
    assert STAGE_NAME_REP_COMPARISON == "rep_comparison"


def test_default_stage_list_runs_rep_comparison_after_per_rep_metrics_and_before_chain_reasoning():
    names = [s.name for s in _default_stage_list()]
    assert STAGE_NAME_REP_COMPARISON in names
    assert names.index(STAGE_NAME_PER_REP_METRICS) < names.index(STAGE_NAME_REP_COMPARISON)
    assert names.index(STAGE_NAME_REP_COMPARISON) < names.index(STAGE_NAME_CHAIN_REASONING)


def test_push_up_and_rollup_stage_lists_exclude_rep_comparison():
    push_names = [s.name for s in _push_up_stage_list()]
    rollup_names = [s.name for s in _rollup_stage_list()]
    assert STAGE_NAME_REP_COMPARISON not in push_names
    assert STAGE_NAME_REP_COMPARISON not in rollup_names
