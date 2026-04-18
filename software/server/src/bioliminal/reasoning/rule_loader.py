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
