"""Rule loader — reads YAML rule files from `config/rules/` into `RuleConfig` objects.

MSI cherry-pick stance (per ML#1, 2026-04-19):
    Bioliminal uses the *kinematic patterns* described in the Sahrmann
    Movement-System-Impairment (MSI) literature, but DOES NOT publish MSI
    diagnostic labels in user-facing output. Rationale:

      * Van Dillen LR et al. (2016, n=101 RCT): MSI-classification-specific
        treatment for chronic low back pain showed no advantage over generic
        movement training.
      * Joyce AA et al. (2023, critique): movement-pattern diagnoses have not
        been shown to predict pain, disability, or future injury.
      * Counter-example we DO use: Harris-Hayes M (2014/2018, hip adduction
        during single-leg squat) — a kinematic pattern with a published
        function correlation. That is the rule type we cherry-pick.

    Operationally: every rule loaded by this module must declare an
    `evidence` block (see `EvidenceBlock` in `config_schemas.py`) stating the
    level of evidence, citation, and mechanism. The schema enforces
    presence; this module does not gate on `level`, but downstream report-
    narrative templates may use `level` to soften or strengthen language.
    Narrative templates themselves are scanned for forbidden clinical terms
    by `tests/unit/reasoning/test_wellness_language.py`.

    A rule whose only support is an MSI label without independent kinematic-
    to-outcome evidence should NOT ship. Use `level: mechanism_only` for
    biomechanically plausible but clinically unvalidated rules; use
    `level: expert_consensus` for FMS / Anatomy Trains-style theoretical
    framework rules. Reserve `level: rct` and `level: prospective_cohort`
    for rules with published clinical-outcome data.
"""

from pathlib import Path

import yaml
from pydantic import TypeAdapter

from bioliminal.reasoning.config_schemas import RuleConfig

_RULES_DIR = Path(__file__).resolve().parents[3] / "config" / "rules"

_RuleListAdapter = TypeAdapter(list[RuleConfig])


def load_rules(rules_dir: Path | None = None) -> list[RuleConfig]:
    d = rules_dir or _RULES_DIR
    all_rules: list[RuleConfig] = []
    seen_ids: set[str] = set()
    for yaml_path in sorted(d.glob("*.yaml")):
        raw = yaml.safe_load(yaml_path.read_text())
        rules = _RuleListAdapter.validate_python(raw["rules"])
        for rule in rules:
            if rule.rule_id in seen_ids:
                raise ValueError(f"duplicate rule_id {rule.rule_id!r} found in {yaml_path.name}")
            seen_ids.add(rule.rule_id)
        all_rules.extend(rules)
    return all_rules
