import pytest

from auralink.pipeline.errors import PipelineError
from auralink.pipeline.registry import StageRegistry
from auralink.pipeline.stages.base import Stage


def _noop_stage(name: str) -> Stage:
    return Stage(name=name, run=lambda ctx: None)


def test_register_and_get_stages():
    reg = StageRegistry()
    stages = [_noop_stage("a"), _noop_stage("b")]
    reg.register_movement("overhead_squat", stages)
    assert reg.has_movement("overhead_squat")
    assert [s.name for s in reg.get_stages("overhead_squat")] == ["a", "b"]


def test_register_is_idempotent_last_wins():
    reg = StageRegistry()
    reg.register_movement("overhead_squat", [_noop_stage("a")])
    reg.register_movement("overhead_squat", [_noop_stage("b")])
    assert [s.name for s in reg.get_stages("overhead_squat")] == ["b"]


def test_get_stages_unknown_movement_raises():
    reg = StageRegistry()
    with pytest.raises(PipelineError):
        reg.get_stages("unknown_movement")


def test_get_stages_returns_a_copy():
    reg = StageRegistry()
    reg.register_movement("overhead_squat", [_noop_stage("a")])
    got = reg.get_stages("overhead_squat")
    got.append(_noop_stage("tampered"))
    assert len(reg.get_stages("overhead_squat")) == 1
