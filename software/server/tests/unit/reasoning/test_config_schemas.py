import pytest
from pydantic import ValidationError

from bioliminal.reasoning.chains import ChainName
from bioliminal.reasoning.config_schemas import (
    BodyTypeAdjustment,
    EvidenceBlock,
    RuleConfig,
    ThresholdSetConfig,
)


def _evidence(**overrides) -> EvidenceBlock:
    base = dict(
        level="prospective_cohort",
        citation="Hewett TE et al. Am J Sports Med. 2005;33(4):492-501.",
        mechanism="Dynamic knee valgus correlates with elevated knee abduction moment.",
    )
    base.update(overrides)
    return EvidenceBlock(**base)


def test_threshold_set_config_validates():
    cfg = ThresholdSetConfig(
        knee_valgus_concern=8.0,
        knee_valgus_flag=12.0,
        hip_drop_concern=5.0,
        hip_drop_flag=10.0,
        trunk_lean_concern=6.0,
        trunk_lean_flag=10.0,
    )
    assert cfg.knee_valgus_flag == 12.0


def test_rule_config_validates():
    rule = RuleConfig(
        rule_id="sbl_test",
        chain=ChainName.SBL,
        applies_to_movements=["overhead_squat"],
        metric_key="mean_knee_valgus_deg",
        aggregation="max",
        threshold_concern_ref="knee_valgus_concern",
        threshold_flag_ref="knee_valgus_flag",
        involved_joints=["knee"],
        narrative_template="value {value:.1f}",
        evidence=_evidence(),
    )
    assert rule.confidence == 0.8
    assert rule.chain == ChainName.SBL
    assert rule.evidence.level == "prospective_cohort"


def test_rule_config_rejects_bad_metric_key():
    with pytest.raises(ValidationError):
        RuleConfig(
            rule_id="bad",
            chain=ChainName.SBL,
            applies_to_movements=["overhead_squat"],
            metric_key="not_a_real_metric",
            aggregation="max",
            threshold_concern_ref="x",
            threshold_flag_ref="y",
            narrative_template="n",
            evidence=_evidence(),
        )


def test_rule_config_rejects_missing_evidence():
    with pytest.raises(ValidationError) as exc_info:
        RuleConfig(
            rule_id="missing_evidence",
            chain=ChainName.SBL,
            applies_to_movements=["overhead_squat"],
            metric_key="mean_knee_valgus_deg",
            aggregation="max",
            threshold_concern_ref="knee_valgus_concern",
            threshold_flag_ref="knee_valgus_flag",
            narrative_template="n",
        )
    assert "evidence" in str(exc_info.value).lower()


def test_evidence_block_rejects_bad_level():
    with pytest.raises(ValidationError):
        EvidenceBlock(
            level="anecdote",  # not in EvidenceLevel literal
            citation="x",
            mechanism="y",
        )


def test_evidence_block_rejects_empty_citation():
    with pytest.raises(ValidationError):
        EvidenceBlock(level="rct", citation="", mechanism="ok")


def test_evidence_block_accepts_optional_fields():
    ev = EvidenceBlock(
        level="cross_sectional",
        citation="Harris-Hayes M et al. JOSPT. 2014;44(11):890-898.",
        mechanism="Hip adduction angle reflects abductor recruitment.",
        correlation="r = -0.67, p < 0.01",
        notes="Cross-sectional only; symptomatic population.",
    )
    assert ev.correlation == "r = -0.67, p < 0.01"
    assert ev.notes is not None


def test_body_type_adjustment_defaults():
    adj = BodyTypeAdjustment()
    assert adj.applies_to_sex == []
    assert adj.applies_to_hypermobile is None
    assert adj.applies_to_age_range == []
    assert adj.threshold_overrides == {}
