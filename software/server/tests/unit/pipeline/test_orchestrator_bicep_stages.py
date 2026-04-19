from bioliminal.pipeline.orchestrator import _bicep_curl_stage_list
from bioliminal.pipeline.stages.base import STAGE_NAME_REP_SEGMENT, STAGE_NAME_PER_REP_METRICS


def test_bicep_stage_list_includes_rep_segment_and_per_rep_metrics():
    names = [s.name for s in _bicep_curl_stage_list()]
    assert STAGE_NAME_REP_SEGMENT in names
    assert STAGE_NAME_PER_REP_METRICS in names


def test_bicep_stage_list_order_is_rep_segment_before_per_rep_metrics():
    names = [s.name for s in _bicep_curl_stage_list()]
    assert names.index(STAGE_NAME_REP_SEGMENT) < names.index(STAGE_NAME_PER_REP_METRICS)


def test_bicep_stage_list_still_ends_with_chain_reasoning():
    from bioliminal.pipeline.stages.base import STAGE_NAME_CHAIN_REASONING
    names = [s.name for s in _bicep_curl_stage_list()]
    assert names[-1] == STAGE_NAME_CHAIN_REASONING
