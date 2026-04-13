import pytest
from pydantic import ValidationError

from auralink.reasoning.chains import ChainName
from auralink.reasoning.config_schemas import (
    BodyTypeAdjustment,
    RuleConfig,
    ThresholdSetConfig,
)


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
    )
    assert rule.confidence == 0.8
    assert rule.chain == ChainName.SBL


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
        )


def test_body_type_adjustment_defaults():
    adj = BodyTypeAdjustment()
    assert adj.applies_to_sex == []
    assert adj.applies_to_hypermobile is None
    assert adj.applies_to_age_range == []
    assert adj.threshold_overrides == {}
