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
