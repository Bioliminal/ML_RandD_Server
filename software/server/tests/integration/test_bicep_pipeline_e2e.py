import pytest

from bioliminal.pipeline.orchestrator import run_pipeline
from tests.fixtures.synthetic_bicep_session import synthetic_bicep_session


def test_clean_10_rep_session_produces_report_with_no_concerns():
    # 180 samples/rep at 30fps = 6s/rep, 3s concentric — above momentum_bias threshold (2s).
    session = synthetic_bicep_session(n_reps=10, samples_per_rep=180,
                                       peak_flexion_deg=50.0, full_extension_deg=170.0)
    report = run_pipeline(session)
    assert report.quality_report.issues == [] or all(
        i.code != "low_upper_limb_visibility" for i in report.quality_report.issues
    )
    bicep_obs = [o for o in (report.chain_observations or []) if o.trigger_rule.startswith("bicep_")]
    assert bicep_obs == []


def test_short_rom_session_triggers_short_rom_rule():
    session = synthetic_bicep_session(n_reps=10, samples_per_rep=90,
                                       peak_flexion_deg=110.0, full_extension_deg=170.0)
    report = run_pipeline(session)
    trigger_rules = {o.trigger_rule for o in (report.chain_observations or [])}
    assert "bicep_short_rom" in trigger_rules


def test_rep_scores_populated_with_elbow_angle_range():
    session = synthetic_bicep_session(n_reps=10, samples_per_rep=90,
                                       peak_flexion_deg=50.0, full_extension_deg=170.0)
    report = run_pipeline(session)
    assert report.rep_scores is not None
    assert len(report.rep_scores) == 10
    for rs in report.rep_scores:
        assert rs.elbow_angle_range is not None
        lo, hi = rs.elbow_angle_range
        assert 40.0 <= lo <= 60.0
        assert 160.0 <= hi <= 180.0


def test_momentum_bias_triggers_on_fast_concentric():
    session = synthetic_bicep_session(n_reps=10, samples_per_rep=20,
                                       peak_flexion_deg=50.0, full_extension_deg=170.0)
    report = run_pipeline(session)
    trigger_rules = {o.trigger_rule for o in (report.chain_observations or [])}
    assert "bicep_momentum_bias" in trigger_rules
