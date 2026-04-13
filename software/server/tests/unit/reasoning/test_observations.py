import pytest
from pydantic import ValidationError

from auralink.reasoning.chains import ChainName
from auralink.reasoning.observations import ChainObservation, ObservationSeverity


def test_creates_observation():
    obs = ChainObservation(
        chain=ChainName.SBL,
        severity=ObservationSeverity.CONCERN,
        confidence=0.8,
        trigger_rule="sbl_knee_valgus_concern",
        involved_joints=["ankle", "knee", "hip"],
        evidence={"mean_knee_valgus_deg": 9.5},
        narrative="Your knee tracking shows 9.5 degrees of inward movement.",
    )
    assert obs.chain == ChainName.SBL
    assert obs.severity == ObservationSeverity.CONCERN
    assert obs.involved_joints == ["ankle", "knee", "hip"]


def test_rejects_confidence_above_one():
    with pytest.raises(ValidationError):
        ChainObservation(
            chain=ChainName.SBL,
            severity=ObservationSeverity.INFO,
            confidence=1.5,
            trigger_rule="x",
            narrative="n",
        )


def test_serializes_to_dict_with_chain_value():
    obs = ChainObservation(
        chain=ChainName.BFL,
        severity=ObservationSeverity.FLAG,
        confidence=0.9,
        trigger_rule="bfl_test",
        narrative="n",
    )
    data = obs.model_dump(mode="json")
    assert data["chain"] == "back_functional_line"
    assert data["severity"] == "flag"
