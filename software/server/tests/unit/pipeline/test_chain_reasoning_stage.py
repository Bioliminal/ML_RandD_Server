from datetime import UTC, datetime

from auralink.api.schemas import Session, SessionMetadata
from auralink.pipeline.stages.base import STAGE_NAME_PER_REP_METRICS, StageContext
from auralink.pipeline.stages.chain_reasoning import run_chain_reasoning
from auralink.reasoning.chains import ChainName
from auralink.reasoning.observations import ChainObservation, ObservationSeverity


class _FakeReasoner:
    def __init__(self, observations: list[ChainObservation]):
        self._observations = observations
        self.calls: list[tuple] = []

    def reason(self, per_rep_metrics, movement, body_type=None):
        self.calls.append((per_rep_metrics, movement, body_type))
        return list(self._observations)


def _ctx(movement: str = "overhead_squat") -> StageContext:
    session = Session(
        metadata=SessionMetadata(
            movement=movement,
            device="test",
            model="test",
            frame_rate=30.0,
            captured_at=datetime.now(UTC),
        ),
        frames=[],
    )
    return StageContext(session=session)


def test_run_chain_reasoning_returns_empty_when_per_rep_missing():
    ctx = _ctx()
    fake = _FakeReasoner([])
    result = run_chain_reasoning(ctx, reasoner=fake)
    assert result == []
    assert fake.calls == [(None, "overhead_squat", None)]


def test_run_chain_reasoning_passes_movement_and_per_rep_to_reasoner():
    ctx = _ctx(movement="single_leg_squat")
    ctx.artifacts[STAGE_NAME_PER_REP_METRICS] = "sentinel-per-rep"
    fake = _FakeReasoner([])
    run_chain_reasoning(ctx, reasoner=fake)
    assert fake.calls == [("sentinel-per-rep", "single_leg_squat", None)]


def test_run_chain_reasoning_returns_reasoner_observations_unchanged():
    obs_a = ChainObservation(
        chain=ChainName.SBL,
        severity=ObservationSeverity.CONCERN,
        confidence=0.8,
        trigger_rule="sbl_a",
        narrative="a",
    )
    obs_b = ChainObservation(
        chain=ChainName.BFL,
        severity=ObservationSeverity.FLAG,
        confidence=0.7,
        trigger_rule="bfl_b",
        narrative="b",
    )
    ctx = _ctx()
    ctx.artifacts[STAGE_NAME_PER_REP_METRICS] = "x"
    fake = _FakeReasoner([obs_a, obs_b])
    result = run_chain_reasoning(ctx, reasoner=fake)
    assert result == [obs_a, obs_b]
