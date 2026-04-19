from pathlib import Path

import pytest
from pydantic import ValidationError

from bioliminal.reasoning.rule_loader import load_rules


def _write_rule_file(path: Path, rule_id: str, chain: str) -> None:
    path.write_text(
        "rules:\n"
        f"  - rule_id: {rule_id}\n"
        f"    chain: {chain}\n"
        "    applies_to_movements: [overhead_squat]\n"
        "    metric_key: mean_knee_valgus_deg\n"
        "    aggregation: max\n"
        "    threshold_concern_ref: knee_valgus_concern\n"
        "    threshold_flag_ref: knee_valgus_flag\n"
        "    involved_joints: [knee]\n"
        '    narrative_template: "value {value:.1f}"\n'
        "    confidence: 0.8\n"
        "    evidence:\n"
        "      level: prospective_cohort\n"
        '      citation: "Hewett TE et al. Am J Sports Med. 2005;33(4):492-501."\n'
        '      mechanism: "Knee valgus correlates with elevated abduction moment."\n'
    )


def test_loads_multi_file_rules_directory(tmp_path: Path):
    _write_rule_file(tmp_path / "sbl.yaml", "sbl_x", "superficial_back_line")
    _write_rule_file(tmp_path / "bfl.yaml", "bfl_y", "back_functional_line")
    rules = load_rules(tmp_path)
    rule_ids = {r.rule_id for r in rules}
    assert rule_ids == {"sbl_x", "bfl_y"}


def test_loads_sorts_files_alphabetically(tmp_path: Path):
    _write_rule_file(tmp_path / "z.yaml", "z_rule", "superficial_back_line")
    _write_rule_file(tmp_path / "a.yaml", "a_rule", "superficial_back_line")
    rules = load_rules(tmp_path)
    assert [r.rule_id for r in rules] == ["a_rule", "z_rule"]


def test_rejects_malformed_rule(tmp_path: Path):
    (tmp_path / "bad.yaml").write_text(
        "rules:\n"
        "  - rule_id: bad\n"
        "    chain: not_a_real_chain\n"
        "    applies_to_movements: [overhead_squat]\n"
        "    metric_key: mean_knee_valgus_deg\n"
        "    aggregation: max\n"
        "    threshold_concern_ref: x\n"
        "    threshold_flag_ref: y\n"
        '    narrative_template: "n"\n'
        "    evidence:\n"
        "      level: rct\n"
        '      citation: "x"\n'
        '      mechanism: "y"\n'
    )
    with pytest.raises(ValidationError):
        load_rules(tmp_path)


def test_rejects_rule_missing_evidence_block(tmp_path: Path):
    (tmp_path / "no_evidence.yaml").write_text(
        "rules:\n"
        "  - rule_id: no_evidence\n"
        "    chain: superficial_back_line\n"
        "    applies_to_movements: [overhead_squat]\n"
        "    metric_key: mean_knee_valgus_deg\n"
        "    aggregation: max\n"
        "    threshold_concern_ref: knee_valgus_concern\n"
        "    threshold_flag_ref: knee_valgus_flag\n"
        "    involved_joints: [knee]\n"
        '    narrative_template: "value {value:.1f}"\n'
        "    confidence: 0.8\n"
    )
    with pytest.raises(ValidationError) as exc_info:
        load_rules(tmp_path)
    assert "evidence" in str(exc_info.value).lower()


def test_rejects_duplicate_rule_id_across_files(tmp_path: Path):
    _write_rule_file(tmp_path / "sbl.yaml", "shared_id", "superficial_back_line")
    _write_rule_file(tmp_path / "bfl.yaml", "shared_id", "back_functional_line")
    with pytest.raises(ValueError, match="duplicate rule_id"):
        load_rules(tmp_path)
