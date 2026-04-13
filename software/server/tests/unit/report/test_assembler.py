from auralink.pipeline.artifacts import PipelineArtifacts, SessionQualityReport
from auralink.reasoning.chains import ChainName
from auralink.reasoning.observations import ChainObservation, ObservationSeverity
from auralink.report.assembler import assemble_report


def _artifacts(chain_observations=None) -> PipelineArtifacts:
    return PipelineArtifacts(
        quality_report=SessionQualityReport(passed=True),
        chain_observations=chain_observations,
    )


def _flag_obs() -> ChainObservation:
    return ChainObservation(
        chain=ChainName.SBL,
        severity=ObservationSeverity.FLAG,
        confidence=0.8,
        trigger_rule="sbl_flag",
        narrative="n",
    )


def _concern_obs() -> ChainObservation:
    return ChainObservation(
        chain=ChainName.BFL,
        severity=ObservationSeverity.CONCERN,
        confidence=0.7,
        trigger_rule="bfl_concern",
        narrative="n",
    )


def test_assemble_with_no_observations_produces_clean_narrative():
    report = assemble_report(
        artifacts=_artifacts([]),
        session_id="s1",
        movement="overhead_squat",
    )
    assert "clean overall pattern" in report.overall_narrative
    assert report.movement_section.chain_observations == []


def test_assemble_with_one_flag_observation():
    report = assemble_report(
        artifacts=_artifacts([_flag_obs()]),
        session_id="s1",
        movement="overhead_squat",
    )
    assert "notable pattern" in report.overall_narrative
    assert len(report.movement_section.chain_observations) == 1


def test_assemble_copies_artifacts_fields_into_movement_section():
    artifacts = _artifacts([])
    report = assemble_report(
        artifacts=artifacts,
        session_id="s1",
        movement="overhead_squat",
        captured_at_ms=1234,
    )
    assert report.metadata.session_id == "s1"
    assert report.metadata.movement == "overhead_squat"
    assert report.metadata.captured_at_ms == 1234
    assert report.movement_section.movement == "overhead_squat"


def test_assemble_with_concern_and_flag_produces_compound_narrative():
    report = assemble_report(
        artifacts=_artifacts([_flag_obs(), _concern_obs()]),
        session_id="s1",
        movement="overhead_squat",
    )
    assert "notable pattern" in report.overall_narrative
    assert "early-stage variation" in report.overall_narrative
