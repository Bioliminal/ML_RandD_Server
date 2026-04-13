from auralink.pipeline.artifacts import PipelineArtifacts, SessionQualityReport
from auralink.reasoning.chains import ChainName
from auralink.reasoning.observations import ChainObservation, ObservationSeverity


def test_pipeline_artifacts_accepts_chain_observations():
    obs = ChainObservation(
        chain=ChainName.SBL,
        severity=ObservationSeverity.CONCERN,
        confidence=0.75,
        trigger_rule="sbl_rule",
        narrative="n",
    )
    artifacts = PipelineArtifacts(
        quality_report=SessionQualityReport(passed=True),
        chain_observations=[obs],
    )
    data = artifacts.model_dump()
    restored = PipelineArtifacts.model_validate(data)
    assert restored.chain_observations is not None
    assert len(restored.chain_observations) == 1
    assert restored.chain_observations[0].trigger_rule == "sbl_rule"
