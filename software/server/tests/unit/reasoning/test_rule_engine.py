from bioliminal.pipeline.artifacts import PerRepMetrics, RepMetric
from bioliminal.reasoning.body_type import BodyTypeProfile
from bioliminal.reasoning.chains import ChainName
from bioliminal.reasoning.config_schemas import (
    BodyTypeAdjustment,
    BodyTypeAdjustmentsConfig,
    RuleConfig,
    ThresholdSetConfig,
)
from bioliminal.reasoning.observations import ObservationSeverity
from bioliminal.reasoning.rule_engine import RuleBasedChainReasoner


def _rep(valgus: float = 0.0, trunk_lean: float = 0.0) -> RepMetric:
    return RepMetric(
        rep_index=0,
        amplitude_deg=90.0,
        peak_velocity_deg_per_s=180.0,
        rom_deg=90.0,
        mean_trunk_lean_deg=trunk_lean,
        mean_knee_valgus_deg=valgus,
    )


def _per_rep(reps: list[RepMetric]) -> PerRepMetrics:
    return PerRepMetrics(primary_angle="knee_flexion", reps=reps)


def _thresholds() -> ThresholdSetConfig:
    return ThresholdSetConfig(
        knee_valgus_concern=8.0,
        knee_valgus_flag=12.0,
        hip_drop_concern=5.0,
        hip_drop_flag=10.0,
        trunk_lean_concern=6.0,
        trunk_lean_flag=10.0,
    )


def _valgus_rule() -> RuleConfig:
    return RuleConfig(
        rule_id="sbl_knee_valgus_concern",
        chain=ChainName.SBL,
        applies_to_movements=["overhead_squat"],
        metric_key="mean_knee_valgus_deg",
        aggregation="max",
        threshold_concern_ref="knee_valgus_concern",
        threshold_flag_ref="knee_valgus_flag",
        involved_joints=["ankle", "knee", "hip"],
        narrative_template="knee valgus {value:.1f}",
        confidence=0.75,
    )


def test_returns_empty_when_per_rep_metrics_is_none():
    reasoner = RuleBasedChainReasoner(
        rules=[_valgus_rule()],
        base_thresholds=_thresholds(),
        adjustments=BodyTypeAdjustmentsConfig(),
    )
    assert reasoner.reason(None, "overhead_squat") == []


def test_rule_fires_at_concern_severity():
    per_rep = _per_rep([_rep(valgus=9.5)])
    reasoner = RuleBasedChainReasoner(
        rules=[_valgus_rule()],
        base_thresholds=_thresholds(),
        adjustments=BodyTypeAdjustmentsConfig(),
    )
    obs = reasoner.reason(per_rep, "overhead_squat")
    assert len(obs) == 1
    assert obs[0].severity == ObservationSeverity.CONCERN
    assert obs[0].chain == ChainName.SBL


def test_rule_fires_at_flag_severity():
    per_rep = _per_rep([_rep(valgus=13.0)])
    reasoner = RuleBasedChainReasoner(
        rules=[_valgus_rule()],
        base_thresholds=_thresholds(),
        adjustments=BodyTypeAdjustmentsConfig(),
    )
    obs = reasoner.reason(per_rep, "overhead_squat")
    assert len(obs) == 1
    assert obs[0].severity == ObservationSeverity.FLAG


def test_rule_skipped_when_movement_does_not_match():
    per_rep = _per_rep([_rep(valgus=13.0)])
    reasoner = RuleBasedChainReasoner(
        rules=[_valgus_rule()],
        base_thresholds=_thresholds(),
        adjustments=BodyTypeAdjustmentsConfig(),
    )
    assert reasoner.reason(per_rep, "push_up") == []


def test_body_type_adjustment_raises_threshold_so_rule_does_not_fire():
    per_rep = _per_rep([_rep(valgus=9.5)])
    adjustments = BodyTypeAdjustmentsConfig(
        adjustments=[
            BodyTypeAdjustment(
                applies_to_hypermobile=True,
                threshold_overrides={
                    "knee_valgus_concern": 10.0,
                    "knee_valgus_flag": 15.0,
                },
            )
        ]
    )
    reasoner = RuleBasedChainReasoner(
        rules=[_valgus_rule()],
        base_thresholds=_thresholds(),
        adjustments=adjustments,
    )
    profile = BodyTypeProfile(hypermobile=True)
    assert reasoner.reason(per_rep, "overhead_squat", body_type=profile) == []


def test_narrative_template_formats_value():
    per_rep = _per_rep([_rep(valgus=9.5)])
    reasoner = RuleBasedChainReasoner(
        rules=[_valgus_rule()],
        base_thresholds=_thresholds(),
        adjustments=BodyTypeAdjustmentsConfig(),
    )
    obs = reasoner.reason(per_rep, "overhead_squat")
    assert obs[0].narrative == "knee valgus 9.5"
