import re
from pathlib import Path

import yaml

_FORBIDDEN_TERMS = [
    "diagnosis",
    "dysfunction",
    "drivers of pain",
    "injury",
    "damage",
    "pathology",
]

_RULES_DIR = Path(__file__).resolve().parents[3] / "config" / "rules"


def test_no_forbidden_wellness_terms_in_rule_narratives():
    violations: list[str] = []
    for yaml_path in sorted(_RULES_DIR.glob("*.yaml")):
        data = yaml.safe_load(yaml_path.read_text())
        for rule in data.get("rules", []):
            narrative = rule.get("narrative_template", "")
            for term in _FORBIDDEN_TERMS:
                if re.search(rf"\b{re.escape(term)}\b", narrative, re.IGNORECASE):
                    rule_id = rule.get("rule_id")
                    violations.append(
                        f"{yaml_path.name}:{rule_id} contains forbidden term "
                        f"'{term}': {narrative!r}"
                    )
    assert not violations, "wellness-language violations:\n" + "\n".join(violations)
