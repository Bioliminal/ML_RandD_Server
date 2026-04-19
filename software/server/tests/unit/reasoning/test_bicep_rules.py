import pytest

from bioliminal.pipeline.artifacts import PerRepMetrics, RepMetric
from bioliminal.reasoning.observations import ObservationSeverity
from bioliminal.reasoning.rule_loader import load_rules
from bioliminal.reasoning.threshold_loader import load_default_thresholds, load_body_type_adjustments
from bioliminal.reasoning.rule_engine import RuleBasedChainReasoner


def _mk_metrics(*, amplitude: float, concentric_s: float, velocity_decline: float,
                amp_cv: float, tempo_cv: float, n: int = 10) -> PerRepMetrics:
    reps = [
        RepMetric(
            rep_index=i,
            amplitude_deg=amplitude,
            peak_velocity_deg_per_s=100.0,
            rom_deg=amplitude,
            mean_trunk_lean_deg=0.0,
            mean_knee_valgus_deg=0.0,
            concentric_s=concentric_s,
            eccentric_s=concentric_s,
            velocity_decline_pct=velocity_decline,
            amplitude_cv_pct=amp_cv,
            tempo_cv_pct=tempo_cv,
        )
        for i in range(n)
    ]
    return PerRepMetrics(primary_angle="left_elbow_flexion", reps=reps)


@pytest.fixture
def reasoner():
    rules = load_rules()
    thresholds = load_default_thresholds()
    adjustments = load_body_type_adjustments()
    return RuleBasedChainReasoner(rules=rules, base_thresholds=thresholds, adjustments=adjustments)


def test_short_rom_fires_concern_at_95_deg(reasoner):
    metrics = _mk_metrics(amplitude=95.0, concentric_s=2.5, velocity_decline=0.05,
                          amp_cv=5.0, tempo_cv=5.0)
    obs = reasoner.reason(metrics, movement="bicep_curl")
    ids = {o.trigger_rule: o.severity for o in obs}
    assert ids.get("bicep_short_rom") == ObservationSeverity.CONCERN


def test_short_rom_fires_flag_at_75_deg(reasoner):
    metrics = _mk_metrics(amplitude=75.0, concentric_s=2.5, velocity_decline=0.05,
                          amp_cv=5.0, tempo_cv=5.0)
    obs = reasoner.reason(metrics, movement="bicep_curl")
    ids = {o.trigger_rule: o.severity for o in obs}
    assert ids.get("bicep_short_rom") == ObservationSeverity.FLAG


def test_healthy_rep_pack_fires_no_bicep_rules(reasoner):
    metrics = _mk_metrics(amplitude=120.0, concentric_s=2.5, velocity_decline=0.05,
                          amp_cv=5.0, tempo_cv=5.0)
    obs = reasoner.reason(metrics, movement="bicep_curl")
    assert [o.trigger_rule for o in obs if o.trigger_rule.startswith("bicep_")] == []


def test_velocity_decline_fires_flag_at_30_pct(reasoner):
    metrics = _mk_metrics(amplitude=120.0, concentric_s=2.5, velocity_decline=0.30,
                          amp_cv=5.0, tempo_cv=5.0)
    obs = reasoner.reason(metrics, movement="bicep_curl")
    ids = {o.trigger_rule: o.severity for o in obs}
    assert ids.get("bicep_velocity_decline") == ObservationSeverity.FLAG


def test_momentum_bias_fires_at_fast_concentric(reasoner):
    metrics = _mk_metrics(amplitude=120.0, concentric_s=0.8, velocity_decline=0.05,
                          amp_cv=5.0, tempo_cv=5.0)
    obs = reasoner.reason(metrics, movement="bicep_curl")
    ids = {o.trigger_rule: o.severity for o in obs}
    assert ids.get("bicep_momentum_bias") == ObservationSeverity.FLAG


def test_narrative_template_renders_with_metric_value(reasoner):
    metrics = _mk_metrics(amplitude=75.0, concentric_s=2.5, velocity_decline=0.05,
                          amp_cv=5.0, tempo_cv=5.0)
    obs = reasoner.reason(metrics, movement="bicep_curl")
    short_rom = next(o for o in obs if o.trigger_rule == "bicep_short_rom")
    assert "75°" in short_rom.narrative or "75" in short_rom.narrative
    forbidden = ["diagnosis", "dysfunction", "injury", "clinical", "MVC"]
    for word in forbidden:
        assert word.lower() not in short_rom.narrative.lower()


def test_squat_rules_do_not_apply_to_bicep_movement(reasoner):
    metrics = _mk_metrics(amplitude=120.0, concentric_s=2.5, velocity_decline=0.05,
                          amp_cv=5.0, tempo_cv=5.0)
    obs = reasoner.reason(metrics, movement="bicep_curl")
    for o in obs:
        assert not o.trigger_rule.startswith("sbl_")
        assert not o.trigger_rule.startswith("bfl_")
        assert not o.trigger_rule.startswith("ffl_")
