from unittest.mock import patch

from auralink.pipeline.orchestrator import (
    _assemble_artifacts,
    _default_stage_list,
    _push_up_stage_list,
    _rollup_stage_list,
)
from auralink.pipeline.stages.base import (
    STAGE_NAME_CHAIN_REASONING,
    STAGE_NAME_QUALITY_GATE,
    Stage,
    StageContext,
)


def _stage_names(stages) -> list[str]:
    return [s.name for s in stages]


def test_default_stage_list_ends_with_chain_reasoning():
    names = _stage_names(_default_stage_list())
    assert "chain_reasoning" in names
    assert names[-1] == "chain_reasoning"


def test_push_up_stage_list_ends_with_chain_reasoning():
    names = _stage_names(_push_up_stage_list())
    assert "chain_reasoning" in names
    assert names[-1] == "chain_reasoning"


def test_rollup_stage_list_does_not_contain_chain_reasoning():
    names = _stage_names(_rollup_stage_list())
    assert "chain_reasoning" not in names


def test_assemble_artifacts_populates_chain_observations():
    """_assemble_artifacts must copy chain_reasoning stage output onto PipelineArtifacts."""
    class _FakeSession:
        class metadata:
            movement = "overhead_squat"

    ctx = StageContext.__new__(StageContext)
    ctx.session = _FakeSession()
    ctx.artifacts = {
        STAGE_NAME_QUALITY_GATE: object(),
        STAGE_NAME_CHAIN_REASONING: ["sentinel-observation"],
    }
    ctx.config = {}

    with patch("auralink.pipeline.orchestrator.PipelineArtifacts") as fake_pa:
        _assemble_artifacts(ctx)
        kwargs = fake_pa.call_args.kwargs
        assert kwargs["chain_observations"] == ["sentinel-observation"]


def test_chain_reasoning_return_value_reaches_assemble_artifacts():
    """End-to-end contract: the executor loop must store run_chain_reasoning's
    return value under ctx.artifacts[STAGE_NAME_CHAIN_REASONING], and
    _assemble_artifacts must read it back onto PipelineArtifacts.chain_observations.
    """
    from datetime import UTC, datetime

    from auralink.api.schemas import Session, SessionMetadata
    from auralink.pipeline.artifacts import SessionQualityReport
    from auralink.pipeline.orchestrator import run_pipeline
    from auralink.pipeline.registry import StageRegistry
    from auralink.reasoning.chains import ChainName
    from auralink.reasoning.observations import ChainObservation, ObservationSeverity

    sentinel_obs = ChainObservation(
        chain=ChainName.SBL,
        severity=ObservationSeverity.CONCERN,
        confidence=0.9,
        trigger_rule="sentinel_rule",
        narrative="n",
    )

    def _quality(ctx):
        return SessionQualityReport(passed=True)

    def _chain(ctx):
        return [sentinel_obs]

    registry = StageRegistry()
    registry.register_movement(
        "overhead_squat",
        [
            Stage(name=STAGE_NAME_QUALITY_GATE, run=_quality),
            Stage(name=STAGE_NAME_CHAIN_REASONING, run=_chain),
        ],
    )
    session = Session(
        metadata=SessionMetadata(
            movement="overhead_squat",
            device="t",
            model="t",
            frame_rate=30.0,
            captured_at=datetime.now(UTC),
        ),
        frames=[],
    )
    artifacts = run_pipeline(session, registry=registry)
    assert artifacts.chain_observations == [sentinel_obs]
